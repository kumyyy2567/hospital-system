from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.decorators.http import require_GET, require_POST

from .decorators import role_required
from .forms import (
    AppointmentForm,
    AvailabilityForm,
    DoctorProfileForm,
    InvoiceForm,
    MedicalRecordForm,
    PatientProfileForm,
    PrescriptionForm,
    CallbackRequestForm,
    ReportUploadForm,
    StaffForm,
    PaymentProofForm,
    UserRegisterForm,
)
from .models import (
    Appointment,
    AvailabilitySlot,
    BOOKING_PLATFORM_FEE,
    CallbackRequest,
    DoctorProfile,
    Invoice,
    MedicalRecord,
    Notification,
    PatientProfile,
    Payment,
    Prescription,
    Staff,
    sync_profile_role,
)
from .utils import render_to_pdf
import logging
logger = logging.getLogger(__name__)


HOME_LOCATIONS = ['Malakpet', 'Secunderabad', 'Somajiguda', 'Hitec City']
TPA_PARTNERS = ['Medi Assist', 'Heritage Health', 'FHPL', 'Medsave']
INSURANCE_COMPANIES = ['Aditya Birla', 'HDFC ERGO', 'Reliance General', 'ACKO']
FALLBACK_SPECIALTIES = ['Cardiology', 'Neurology', 'Oncology', 'Gastro', 'Mother & Child', 'Orthopedic']
HOSPITAL_UPI_ID = 'abhishek993526@oksbi'
HOSPITAL_UPI_PAYEE = 'Hospital Appointment Desk'
ONLINE_PAYMENT_METHODS = {'UPI', 'CARD', 'NET_BANKING'}
BOOKING_PAYMENT_METHODS = [
    {
        'value': 'UPI',
        'title': 'UPI',
        'note': f'Fast approval through any UPI app using {HOSPITAL_UPI_ID}.',
        'badge': 'Instant',
    },
    {
        'value': 'CARD',
        'title': 'Card',
        'note': 'Use debit or credit cards for instant confirmation.',
        'badge': 'Secure',
    },
    {
        'value': 'NET_BANKING',
        'title': 'Net Banking',
        'note': 'Complete payment through your bank portal.',
        'badge': 'Bank grade',
    },
    {
        'value': 'PAY_AT_HOSPITAL',
        'title': 'Pay at Hospital',
        'note': 'Reserve now and complete payment at reception.',
        'badge': 'Flexible',
    },
]
FOOTER_GROUPS = [
    {
        'title': 'About Hospital',
        'items': ['Overview', 'Achievements', 'Awards & Recognition', 'Yashoda in News', 'Contact Us'],
    },
    {
        'title': 'Our Doctors',
        'items': ['Find Specialists', 'Doctor Schedules', 'Clinical Excellence', 'Second Opinion', 'Medical Teams'],
    },
    {
        'title': 'Patient Info',
        'items': ['Procedure Cost', 'Diagnostics', 'Diseases & Treatments', 'Surgery Care', 'Patient Guide'],
    },
    {
        'title': 'Education',
        'items': ['Introduction', 'Medical Courses', 'Nursing Support', 'Paramedical Courses', 'Health Tips'],
    },
    {
        'title': 'International Care',
        'items': ['Why Choose Us', 'Patient Care', 'Facilities', 'Health Insurance', 'Testimonials'],
    },
]


def index(request):
    return render(request, 'core/index.html', build_homepage_context())


def sync_owner_admin_role(user):
    return sync_profile_role(user)


def wants_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')


def resolve_doctor_location(profile, user_id):
    location = getattr(profile, 'location', '').strip()
    if location:
        return location
    return HOME_LOCATIONS[(user_id - 1) % len(HOME_LOCATIONS)]


def build_experience_label(experience_years):
    if experience_years:
        return f'{experience_years}+ yrs experience'
    return 'Consultant available'


def build_specialty_summaries(limit=6):
    specialties = list(
        DoctorProfile.objects.exclude(specialization='')
        .values('specialization')
        .annotate(total_doctors=Count('id'))
        .order_by('-total_doctors', 'specialization')[:limit]
    )
    if specialties:
        return [
            {
                'name': item['specialization'],
                'total_doctors': item['total_doctors'],
            }
            for item in specialties
        ]
    return [{'name': name, 'total_doctors': 0} for name in FALLBACK_SPECIALTIES[:limit]]


def build_open_slot_map():
    return {
        item['doctor_id']: item['total_slots']
        for item in AvailabilitySlot.objects.filter(is_booked=False, date__gte=date.today())
        .values('doctor_id')
        .annotate(total_slots=Count('id'))
    }


def serialize_doctor_profile(profile, open_slot_map):
    open_slots = open_slot_map.get(profile.user_id, 0)
    next_slot = (
        AvailabilitySlot.objects.filter(doctor=profile.user, is_booked=False, date__gte=date.today())
        .order_by('date', 'start_time')
        .first()
    )
    location = resolve_doctor_location(profile, profile.user_id)
    experience_years = getattr(profile, 'experience_years', 0)
    return {
        'id': profile.user_id,
        'name': profile.user.get_full_name() or profile.user.username,
        'specialization': profile.specialization or 'General Medicine',
        'location': location,
        'experience_years': experience_years,
        'experience_label': build_experience_label(experience_years),
        'fee': float(profile.fee or 0),
        'open_slots': open_slots,
        'phone': profile.phone,
        'next_slot': (
            f'{next_slot.date} {next_slot.start_time.strftime("%H:%M")}'
            if next_slot
            else 'No open slot today'
        ),
    }


def build_booking_doctor_cards(doctors, slots):
    slot_counts = {}
    next_slot_map = {}
    for slot in slots:
        slot_counts[slot.doctor_id] = slot_counts.get(slot.doctor_id, 0) + 1
        next_slot_map.setdefault(slot.doctor_id, slot)

    cards = []
    for doctor in doctors:
        profile = getattr(doctor, 'doctorprofile', None)
        full_name = doctor.get_full_name() or doctor.username
        initials = ''.join(part[0] for part in full_name.split()[:2]).upper() or doctor.username[:2].upper()
        next_slot = next_slot_map.get(doctor.id)
        specialization = getattr(profile, 'specialization', '') or 'General Consultation'
        location = resolve_doctor_location(profile, doctor.id)
        experience_years = getattr(profile, 'experience_years', 0)
        cards.append({
            'id': doctor.id,
            'name': full_name,
            'specialization': specialization,
            'location': location,
            'experience_years': experience_years,
            'experience_label': build_experience_label(experience_years),
            'fee': float(getattr(profile, 'fee', 0) or 0),
            'open_slots': slot_counts.get(doctor.id, 0),
            'next_slot': (
                f'{next_slot.date.strftime("%b %d, %Y")} at {next_slot.start_time.strftime("%H:%M")}'
                if next_slot
                else 'No open slots available'
            ),
            'initials': initials,
            'search_text': f'{full_name} {specialization} {location}'.lower(),
        })
    return cards


def build_home_live_stats():
    return {
        'total_doctors': DoctorProfile.objects.count(),
        'total_patients': PatientProfile.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'open_slots': AvailabilitySlot.objects.filter(is_booked=False, date__gte=date.today()).count(),
        'callback_requests': CallbackRequest.objects.count(),
    }


def build_homepage_context():
    open_slot_map = build_open_slot_map()
    featured_profiles = DoctorProfile.objects.select_related('user').order_by('specialization', 'user__first_name')[:6]
    specialty_summaries = build_specialty_summaries()
    return {
        'callback_form': CallbackRequestForm(),
        'featured_doctors': [serialize_doctor_profile(profile, open_slot_map) for profile in featured_profiles],
        'specialty_summaries': specialty_summaries,
        'home_stats': build_home_live_stats(),
        'hospital_locations': HOME_LOCATIONS,
        'tpa_partners': TPA_PARTNERS,
        'insurance_companies': INSURANCE_COMPANIES,
        'footer_groups': FOOTER_GROUPS,
    }


def build_dashboard_stats(user):
    role = sync_owner_admin_role(user).role
    if role == 'ADMIN':
        total_revenue = Invoice.objects.values_list('total', flat=True)
        return {
            'role': role,
            'total_patients': PatientProfile.objects.count(),
            'total_doctors': DoctorProfile.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'booked_count': Appointment.objects.filter(status='BOOKED').count(),
            'completed_count': Appointment.objects.filter(status='COMPLETED').count(),
            'cancelled_count': Appointment.objects.filter(status='CANCELLED').count(),
            'payments_pending_count': Payment.objects.filter(status='PENDING').count(),
            'payments_under_review_count': Payment.objects.filter(status='UNDER_REVIEW').count(),
            'payments_paid_count': Payment.objects.filter(status='PAID').count(),
            'revenue_sum': float(sum(total_revenue) if total_revenue else 0),
        }
    if role == 'DOCTOR':
        appointment_qs = Appointment.objects.filter(doctor=user)
        return {
            'role': role,
            'doctor_total_appointments': appointment_qs.count(),
            'doctor_completed_appointments': appointment_qs.filter(status='COMPLETED').count(),
            'doctor_open_slots': AvailabilitySlot.objects.filter(doctor=user, is_booked=False).count(),
            'doctor_booked_appointments': appointment_qs.filter(status='BOOKED').count(),
        }
    appointment_qs = Appointment.objects.filter(patient=user)
    return {
        'role': role,
        'patient_total_appointments': appointment_qs.count(),
        'patient_completed_visits': appointment_qs.filter(status='COMPLETED').count(),
        'patient_notifications': user.notifications.filter(is_read=False).count(),
        'patient_upcoming_visits': appointment_qs.filter(status='BOOKED').count(),
    }


def serialize_notifications(user, limit=8):
    return [
        {
            'id': item.id,
            'message': item.message,
            'created_at': localtime(item.created_at).strftime('%b %d, %Y %H:%M'),
            'is_read': item.is_read,
        }
        for item in user.notifications.all()[:limit]
    ]


def signup_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            profile = sync_owner_admin_role(user)
            profile.role = 'PATIENT'
            profile.save(update_fields=['role'])
            PatientProfile.objects.get_or_create(user=user)
            messages.success(request, 'Customer account created. Please log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            sync_owner_admin_role(user)
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid credentials')
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    role = sync_owner_admin_role(request.user).role
    if role == 'ADMIN':
        return redirect('admin_dashboard')
    if role == 'DOCTOR':
        return redirect('doctor_dashboard')
    return redirect('patient_dashboard')


@role_required('ADMIN')
def admin_dashboard(request):
    context = build_dashboard_stats(request.user)
    return render(request, 'core/admin_dashboard.html', context)


@role_required('DOCTOR')
def doctor_dashboard(request):
    appointment_qs = Appointment.objects.filter(doctor=request.user)
    appointments = appointment_qs.order_by('-created_at')[:5]
    records = MedicalRecord.objects.filter(doctor=request.user).order_by('-created_at')[:5]
    context = build_dashboard_stats(request.user)
    context.update({
        'appointments': appointments,
        'records': records,
    })
    return render(request, 'core/doctor_dashboard.html', context)


@role_required('PATIENT')
def patient_dashboard(request):
    appointment_qs = Appointment.objects.filter(patient=request.user)
    appointments = appointment_qs.order_by('-created_at')[:5]
    doctors = User.objects.filter(doctorprofile__isnull=False).select_related('doctorprofile').order_by('first_name', 'username')
    open_slots = list(
        AvailabilitySlot.objects.filter(is_booked=False, date__gte=date.today())
        .select_related('doctor')
        .order_by('date', 'start_time')
    )
    context = build_dashboard_stats(request.user)
    context.update({
        'appointments': appointments,
        'available_doctor_count': doctors.count(),
        'available_slot_count': len(open_slots),
        'featured_doctors': build_booking_doctor_cards(doctors[:6], open_slots),
    })
    return render(request, 'core/patient_dashboard.html', context)


@role_required('ADMIN')
def manage_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff added.')
            return redirect('manage_staff')
    else:
        form = StaffForm()
    staff_list = Staff.objects.all()
    return render(request, 'core/manage_staff.html', {'form': form, 'staff_list': staff_list})


@role_required('ADMIN')
def manage_doctors(request):
    doctors = DoctorProfile.objects.select_related('user').all()
    return render(request, 'core/manage_doctors.html', {'doctors': doctors})


@role_required('DOCTOR')
def availability_create(request):
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = request.user
            slot.save()
            messages.success(request, 'Availability slot added.')
            return redirect('availability_list')
    else:
        form = AvailabilityForm()
    return render(request, 'core/availability_form.html', {'form': form})


@role_required('DOCTOR')
def availability_list(request):
    slots = AvailabilitySlot.objects.filter(doctor=request.user)
    return render(request, 'core/availability_list.html', {'slots': slots})


@role_required('PATIENT')
def book_appointment(request):
    doctors = User.objects.filter(doctorprofile__isnull=False).select_related('doctorprofile', 'profile').order_by('first_name', 'username')
    slots = AvailabilitySlot.objects.filter(is_booked=False, date__gte=date.today()).select_related('doctor').order_by('date', 'start_time')
    
    if not slots.exists():
        messages.warning(request, 'No appointment slots are currently available. Please check back later or contact admin.')
    
    form_kwargs = {
        'doctor_queryset': doctors,
        'slot_queryset': slots,
    }
    if request.method == 'POST':
        form = AppointmentForm(request.POST, **form_kwargs)
        if form.is_valid():
            try:
                with transaction.atomic():
                    slot = form.cleaned_data['slot']
                    slot = AvailabilitySlot.objects.select_for_update().get(pk=slot.pk)
                    if slot.is_booked:
                        messages.error(request, 'The selected slot was taken by another patient. Please choose another.')
                        return redirect('book_appointment')
                    appointment = form.save(commit=False)
                    appointment.patient = request.user
                    appointment.status = 'BOOKED'
                    appointment.save()
                    doctor_profile = getattr(appointment.doctor, 'doctorprofile', None)
                    consultation_fee = Decimal(getattr(doctor_profile, 'fee', 0) or 0)
                    payment_method = form.cleaned_data['payment_method']
                    payment_status = 'PENDING' if payment_method == 'PAY_AT_HOSPITAL' else 'PAID'
                    payment = Payment.objects.create(
                        appointment=appointment,
                        method=payment_method,
                        status=payment_status,
                        consultation_fee=consultation_fee,
                        platform_fee=BOOKING_PLATFORM_FEE,
                        transaction_reference=f"PAY-{appointment.id:05d}-{timezone.now():%H%M%S}",
                        paid_at=timezone.now() if payment_status == 'PAID' else None,
                    )
                    slot.is_booked = True
                    slot.save(update_fields=['is_booked'])
                    logger.info(
                        'Appointment APT-%s booked successfully by %s using %s payment.',
                        appointment.id,
                        request.user.username,
                        payment.get_method_display(),
                    )
            except Exception as e:
                messages.error(request, 'Booking failed due to a system error. Please try again.')
                logger.error(f'Booking error: {str(e)}')
                return redirect('book_appointment')

            doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
            patient_name = appointment.patient.get_full_name() or appointment.patient.username
            if payment.method == 'PAY_AT_HOSPITAL':
                payment_summary = f'Payment of Rs. {payment.total_amount:.0f} pending at hospital'
            else:
                payment_summary = f'Payment of Rs. {payment.total_amount:.0f} confirmed via {payment.get_method_display()}'
            Notification.objects.create(user=request.user, message=f"Appointment booked with Dr. {doctor_name}. {payment_summary}.")
            Notification.objects.create(user=appointment.doctor, message=f"New appointment: {patient_name}. {payment_summary}.")

            send_mail(
                subject='Appointment Confirmation',
                message=(
                    f"Patient: {appointment.patient.get_full_name()}\n"
                    f"Doctor: Dr. {appointment.doctor.get_full_name()}\n"
                    f"Date & Time: {appointment.slot.date} {appointment.slot.start_time}-{appointment.slot.end_time}\n"
                    f"Appointment ID: APT-{appointment.id}\n"
                    f"Payment Method: {payment.get_method_display()}\n"
                    f"Payment Status: {payment.get_status_display()}\n"
                    f"Amount: Rs. {payment.total_amount:.2f}\n"
                    f"Reference: {payment.transaction_reference}"
                ),
                from_email=None,
                recipient_list=[appointment.gmail],
                fail_silently=True,
            )

            messages.success(
                request,
                (
                    f'Appointment APT-{appointment.id} booked successfully. '
                    if payment.status == 'PAID'
                    else f'Appointment APT-{appointment.id} reserved successfully. '
                ) + f'{payment_summary}.'
            )
            return redirect(f"{reverse('patient_appointments')}?booked={appointment.id}")
    else:
        initial = {}
        if request.user.email:
            initial['gmail'] = request.user.email
        initial['payment_method'] = 'UPI'
        selected_doctor = request.GET.get('doctor', '').strip()
        if selected_doctor and doctors.filter(pk=selected_doctor).exists():
            initial['doctor'] = selected_doctor
        form = AppointmentForm(initial=initial, **form_kwargs)

    slot_list = list(slots)
    context = {
        'form': form,
        'booking_platform_fee': BOOKING_PLATFORM_FEE,
        'hospital_upi_id': HOSPITAL_UPI_ID,
        'hospital_upi_payee': HOSPITAL_UPI_PAYEE,
        'payment_methods': BOOKING_PAYMENT_METHODS,
        'doctor_count': doctors.count(),
        'slot_count': len(slot_list),
        'doctor_cards': build_booking_doctor_cards(doctors, slot_list),
    }
    return render(request, 'core/book_appointment.html', context)


@role_required('PATIENT')
def patient_appointments(request):
    query = request.GET.get('q')
    qs = Appointment.objects.filter(patient=request.user).select_related('doctor', 'slot', 'payment').prefetch_related('prescriptions').order_by('-created_at')
    if query:
        qs = qs.filter(doctor__username__icontains=query)
    booked_appointment = None
    booked_id = request.GET.get('booked', '').strip()
    if booked_id.isdigit():
        booked_appointment = qs.filter(pk=int(booked_id)).first()
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    appointments = paginator.get_page(page)
    return render(
        request,
        'core/patient_appointments.html',
        {
            'appointments': appointments,
            'booked_appointment': booked_appointment,
        },
    )


@role_required('PATIENT')
def payment_proof_upload(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('appointment', 'appointment__doctor'),
        pk=payment_id,
        appointment__patient=request.user,
    )
    appointment = payment.appointment

    if payment.method == 'PAY_AT_HOSPITAL':
        messages.info(request, 'This appointment is marked as Pay at Hospital. No screenshot upload is needed.')
        return redirect('patient_appointments')

    if payment.status == 'PAID':
        messages.success(request, 'This payment has already been verified.')
        return redirect('patient_appointments')

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.status = 'UNDER_REVIEW'
            payment.review_note = ''
            payment.verified_at = None
            payment.verified_by = None
            payment.paid_at = payment.paid_at or timezone.now()
            payment.save()

            for admin_user in User.objects.filter(profile__role='ADMIN').distinct():
                Notification.objects.create(
                    user=admin_user,
                    message=(
                        f'Payment proof uploaded for APT-{appointment.id} by '
                        f'{appointment.patient.get_full_name() or appointment.patient.username}.'
                    ),
                )
            Notification.objects.create(
                user=request.user,
                message=f'Payment proof for APT-{appointment.id} submitted and sent for admin verification.',
            )
            messages.success(request, 'Payment proof uploaded successfully. Your booking is now under admin review.')
            return redirect('patient_appointments')
    else:
        form = PaymentProofForm(instance=payment)

    context = {
        'appointment': appointment,
        'payment': payment,
        'form': form,
        'hospital_upi_id': HOSPITAL_UPI_ID,
    }
    return render(request, 'core/payment_proof_form.html', context)


@role_required('DOCTOR')
def doctor_appointments(request):
    query = request.GET.get('q')
    status = request.GET.get('status')
    qs = Appointment.objects.filter(doctor=request.user).select_related('patient', 'slot', 'payment').order_by('-created_at')
    if query:
        qs = qs.filter(patient__username__icontains=query)
    if status:
        qs = qs.filter(status=status)
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    appointments = paginator.get_page(page)
    return render(request, 'core/doctor_appointments.html', {'appointments': appointments})


@role_required('ADMIN')
def manage_payments(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    payments_qs = Payment.objects.select_related(
        'appointment',
        'appointment__patient',
        'appointment__doctor',
        'verified_by',
    ).order_by('-created_at')

    if query:
        payments_qs = payments_qs.filter(
            Q(transaction_reference__icontains=query)
            | Q(transaction_id__icontains=query)
            | Q(appointment__patient__username__icontains=query)
            | Q(appointment__patient__first_name__icontains=query)
            | Q(appointment__doctor__username__icontains=query)
            | Q(appointment__doctor__first_name__icontains=query)
        )
    if status:
        payments_qs = payments_qs.filter(status=status)

    paginator = Paginator(payments_qs, 12)
    payments = paginator.get_page(request.GET.get('page'))
    context = {
        'payments': payments,
        'selected_status': status,
        'payment_statuses': Payment._meta.get_field('status').choices,
        'status_totals': {
            'pending': Payment.objects.filter(status='PENDING').count(),
            'under_review': Payment.objects.filter(status='UNDER_REVIEW').count(),
            'paid': Payment.objects.filter(status='PAID').count(),
            'rejected': Payment.objects.filter(status='REJECTED').count(),
        },
    }
    return render(request, 'core/manage_payments.html', context)


@role_required('ADMIN')
@require_POST
def verify_payment(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('appointment', 'appointment__patient', 'appointment__doctor'),
        pk=payment_id,
    )
    review_note = request.POST.get('review_note', '').strip()
    payment.status = 'PAID'
    payment.review_note = review_note
    payment.verified_at = timezone.now()
    payment.verified_by = request.user
    payment.paid_at = payment.paid_at or timezone.now()
    payment.save(update_fields=['status', 'review_note', 'verified_at', 'verified_by', 'paid_at'])

    Notification.objects.create(
        user=payment.appointment.patient,
        message=(
            f'Payment verified for APT-{payment.appointment.id}. '
            f'Your appointment with Dr. {payment.appointment.doctor.get_full_name() or payment.appointment.doctor.username} is confirmed.'
        ),
    )
    messages.success(request, f'Payment for APT-{payment.appointment.id} marked as paid.')
    return redirect('manage_payments')


@role_required('ADMIN')
@require_POST
def reject_payment(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('appointment', 'appointment__patient'),
        pk=payment_id,
    )
    review_note = request.POST.get('review_note', '').strip() or 'Please upload a clearer payment proof or correct transaction ID.'
    payment.status = 'REJECTED'
    payment.review_note = review_note
    payment.verified_at = None
    payment.verified_by = None
    payment.save(update_fields=['status', 'review_note', 'verified_at', 'verified_by'])

    Notification.objects.create(
        user=payment.appointment.patient,
        message=f'Payment proof for APT-{payment.appointment.id} was rejected. Review the admin note and upload proof again.',
    )
    messages.success(request, f'Payment for APT-{payment.appointment.id} marked as rejected.')
    return redirect('manage_payments')


@role_required('DOCTOR', 'ADMIN')
def update_appointment_status(request, appointment_id, status):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if sync_owner_admin_role(request.user).role == 'DOCTOR' and appointment.doctor != request.user:
        if wants_json(request):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        return HttpResponse('Unauthorized', status=403)
    if status not in ['BOOKED', 'COMPLETED', 'CANCELLED']:
        if wants_json(request):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        return HttpResponse('Invalid status', status=400)
    appointment.status = status
    appointment.save()
    if status == 'CANCELLED':
        slot = appointment.slot
        slot.is_booked = False
        slot.save()
    Notification.objects.create(
        user=appointment.patient,
        message=f'Your appointment APT-{appointment.id} is now {status.lower()}.',
    )
    messages.success(request, f'Appointment marked as {status}.')
    if wants_json(request):
        return JsonResponse({
            'success': True,
            'appointment_id': appointment.id,
            'status': appointment.status,
            'status_label': appointment.get_status_display(),
            'stats': build_dashboard_stats(request.user),
        })
    return redirect('doctor_appointments')


@role_required('DOCTOR')
def add_medical_record(request, patient_id):
    patient = get_object_or_404(User, pk=patient_id)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = request.user
            record.save()
            messages.success(request, 'Medical record updated.')
            return redirect('doctor_appointments')
    else:
        form = MedicalRecordForm()
    return render(request, 'core/medical_record_form.html', {'form': form, 'patient': patient})


@role_required('DOCTOR')
def add_prescription(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=request.user)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.appointment = appointment
            prescription.save()
            messages.success(request, 'Prescription added.')
            return redirect('doctor_appointments')
    else:
        form = PrescriptionForm()
    return render(request, 'core/prescription_form.html', {'form': form, 'appointment': appointment})


@role_required('DOCTOR')
def create_invoice(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=request.user)
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.appointment = appointment
            invoice.save()
            messages.success(request, 'Invoice generated.')
            return redirect('doctor_appointments')
    else:
        form = InvoiceForm()
    return render(request, 'core/invoice_form.html', {'form': form, 'appointment': appointment})


@login_required
def download_appointment_slip(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if request.user != appointment.patient and request.user != appointment.doctor and sync_owner_admin_role(request.user).role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    pdf = render_to_pdf('core/appointment_pdf.html', {'appointment': appointment, 'payment': appointment.payment_record})
    if pdf is None:
        return HttpResponse('PDF generation failed', status=500)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'
    return response


@login_required
def download_prescription(request, prescription_id):
    prescription = get_object_or_404(Prescription, pk=prescription_id)
    appointment = prescription.appointment
    if request.user not in [appointment.patient, appointment.doctor] and sync_owner_admin_role(request.user).role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    pdf = render_to_pdf('core/prescription_pdf.html', {'prescription': prescription})
    if pdf is None:
        return HttpResponse('PDF generation failed', status=500)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    return response


@login_required
def download_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    appointment = invoice.appointment
    if request.user not in [appointment.patient, appointment.doctor] and sync_owner_admin_role(request.user).role != 'ADMIN':
        return HttpResponse('Unauthorized', status=403)
    pdf = render_to_pdf('core/invoice_pdf.html', {'invoice': invoice})
    if pdf is None:
        return HttpResponse('PDF generation failed', status=500)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'
    return response


@role_required('PATIENT')
def upload_report(request):
    if request.method == 'POST':
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.patient = request.user
            report.save()
            messages.success(request, 'Report uploaded.')
            return redirect('patient_dashboard')
    else:
        form = ReportUploadForm()
    return render(request, 'core/report_upload.html', {'form': form})


@login_required
def notifications_panel(request):
    notifications = request.user.notifications.all()
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required
def profile_settings(request):
    role = sync_owner_admin_role(request.user).role
    if role == 'DOCTOR':
        profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        form_class = DoctorProfileForm
    elif role == 'PATIENT':
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        form_class = PatientProfileForm
    else:
        profile = None
        form_class = None
    if request.method == 'POST' and form_class:
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile_settings')
    else:
        form = form_class(instance=profile) if form_class else None
    return render(request, 'core/profile_settings.html', {'form': form, 'role': role})


@role_required('PATIENT')
@require_GET
def available_slots_api(request, doctor_id):
    slots = AvailabilitySlot.objects.filter(
        doctor_id=doctor_id,
        is_booked=False,
        date__gte=date.today(),
    ).order_by('date', 'start_time')
    return JsonResponse({
        'slots': [
            {
                'id': slot.id,
                'label': f'{slot.date.strftime("%a, %b %d")} {slot.start_time.strftime("%H:%M")} - {slot.end_time.strftime("%H:%M")}',
                'date': slot.date.isoformat(),
                'date_label': slot.date.strftime('%a, %b %d'),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'time_label': f'{slot.start_time.strftime("%H:%M")} - {slot.end_time.strftime("%H:%M")}',
            }
            for slot in slots
        ]
    })


@login_required
@require_GET
def dashboard_stats_api(request):
    return JsonResponse(build_dashboard_stats(request.user))


@login_required
@require_GET
def notifications_api(request):
    return JsonResponse({
        'unread_count': request.user.notifications.filter(is_read=False).count(),
        'notifications': serialize_notifications(request.user),
    })


@login_required
@require_POST
def notification_read_api(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return JsonResponse({
        'success': True,
        'unread_count': request.user.notifications.filter(is_read=False).count(),
    })


@login_required
@require_POST
def notifications_mark_all_read_api(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'unread_count': 0})


@require_GET
def home_live_api(request):
    stats = build_home_live_stats()
    stats['specialties'] = build_specialty_summaries()
    return JsonResponse(stats)


@require_GET
def doctor_directory_api(request):
    specialization = request.GET.get('specialty', '').strip()
    open_slot_map = build_open_slot_map()
    profiles = DoctorProfile.objects.select_related('user').all()
    if specialization and specialization.upper() != 'ALL':
        profiles = profiles.filter(specialization__iexact=specialization)
    doctors = [serialize_doctor_profile(profile, open_slot_map) for profile in profiles.order_by('specialization', 'user__first_name')[:12]]
    return JsonResponse({'doctors': doctors})


@require_POST
def callback_request_api(request):
    form = CallbackRequestForm(request.POST)
    if form.is_valid():
        callback_request = form.save()
        return JsonResponse({
            'success': True,
            'message': 'Our care team will call you shortly.',
            'request_id': callback_request.id,
        })
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)
