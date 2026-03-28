from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

ROLE_CHOICES = [
    ('ADMIN', 'Admin'),
    ('DOCTOR', 'Doctor'),
    ('PATIENT', 'Patient'),
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

APPOINTMENT_STATUS = [
    ('BOOKED', 'Booked'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]

CALLBACK_SERVICE_CHOICES = [
    ('GENERAL', 'General Consultation'),
    ('SECOND_OPINION', 'Free Second Opinion'),
    ('INSURANCE', 'Insurance Help'),
    ('MEDICAL_OPINION', 'Medical Opinion'),
]

PAYMENT_METHOD_CHOICES = [
    ('UPI', 'UPI'),
    ('CARD', 'Card'),
    ('NET_BANKING', 'Net Banking'),
    ('PAY_AT_HOSPITAL', 'Pay at Hospital'),
]

PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('UNDER_REVIEW', 'Under Review'),
    ('PAID', 'Paid'),
    ('REJECTED', 'Rejected'),
]

BOOKING_PLATFORM_FEE = Decimal('149.00')


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PATIENT')

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=80, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    phone = models.CharField(max_length=20, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


def get_profile_role_for_user(user):
    if user.is_superuser:
        return 'ADMIN'
    return 'DOCTOR' if DoctorProfile.objects.filter(user=user).exists() else 'PATIENT'


def sync_profile_role(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'role': get_profile_role_for_user(user)},
    )
    expected_role = get_profile_role_for_user(user)
    if profile.role != expected_role:
        profile.role = expected_role
        profile.save(update_fields=['role'])
    return profile


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Other')
    contact = models.CharField(max_length=20, blank=True)
    medical_history = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Staff(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120)
    contact = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.role}"


class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.doctor.username} {self.date} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    slot = models.ForeignKey(AvailabilitySlot, on_delete=models.PROTECT)
    gmail = models.EmailField()
    status = models.CharField(max_length=10, choices=APPOINTMENT_STATUS, default='BOOKED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"APT-{self.id} {self.patient.username} -> {self.doctor.username}"

    @property
    def payment_record(self):
        try:
            return self.payment
        except ObjectDoesNotExist:
            return None


class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records_created')
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Record {self.patient.username} {self.created_at.date()}"


class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    medicines = models.TextField()
    dosage = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription {self.appointment.id}"


class Invoice(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='invoice')
    doctor_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total = (self.doctor_fee or 0) + (self.service_charge or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.appointment.id}"


class Payment(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='UPI')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=BOOKING_PLATFORM_FEE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_reference = models.CharField(max_length=40, blank=True)
    transaction_id = models.CharField(max_length=80, blank=True)
    proof_file = models.FileField(upload_to='payment_proofs/', blank=True)
    submitted_note = models.TextField(blank=True)
    review_note = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_amount = (self.consultation_fee or 0) + (self.platform_fee or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.appointment_id} {self.status}"


class ReportFile(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    file = models.FileField(upload_to='reports/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class CallbackRequest(models.Model):
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20)
    service_type = models.CharField(max_length=20, choices=CALLBACK_SERVICE_CHOICES, default='GENERAL')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.get_service_type_display()}'


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        sync_profile_role(instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    sync_profile_role(instance)


@receiver(post_save, sender=DoctorProfile)
def sync_doctor_role_on_save(sender, instance, **kwargs):
    sync_profile_role(instance.user)


@receiver(post_delete, sender=DoctorProfile)
def sync_doctor_role_on_delete(sender, instance, **kwargs):
    sync_profile_role(instance.user)
