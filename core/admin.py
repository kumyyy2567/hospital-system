from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Profile,
    DoctorProfile,
    PatientProfile,
    AvailabilitySlot,
    Appointment,
    MedicalRecord,
    Payment,
    Prescription,
    Invoice,
    Staff,
    ReportFile,
    Notification,
    CallbackRequest,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'user_is_superuser')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)

    def user_is_superuser(self, obj):
        return obj.user.is_superuser
    user_is_superuser.boolean = True
    user_is_superuser.short_description = 'Superuser'

    actions = ['set_role_admin', 'set_role_patient']

    def set_role_admin(self, request, queryset):
        updated = queryset.update(role='ADMIN')
        self.message_user(request, f'{updated} profiles set to ADMIN.')
    set_role_admin.short_description = 'Set selected to ADMIN role'

    def set_role_patient(self, request, queryset):
        updated = queryset.update(role='PATIENT')
        self.message_user(request, f'{updated} profiles set to PATIENT.')
    set_role_patient.short_description = 'Set selected to PATIENT role'


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'location', 'experience_years', 'phone', 'fee')
    list_filter = ('specialization', 'location')
    search_fields = ('user__username', 'specialization', 'location')
    list_select_related = ('user',)


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'contact')
    list_filter = ('gender', 'age')
    search_fields = ('user__username', 'contact', 'medical_history')
    list_select_related = ('user',)


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = (
        'total_amount',
        'transaction_reference',
        'transaction_id',
        'paid_at',
        'verified_at',
        'verified_by',
        'created_at',
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'slot', 'status', 'created_at')
    list_filter = ('status', 'doctor', 'created_at')
    search_fields = ('patient__username', 'doctor__username', 'gmail')
    list_select_related = ('patient', 'doctor', 'slot')
    inlines = [PaymentInline, PrescriptionInline, InvoiceInline]
    actions = ['mark_completed', 'mark_cancelled']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} appointments marked COMPLETED.')
    mark_completed.short_description = 'Mark selected as COMPLETED'

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} appointments marked CANCELLED.')
    mark_cancelled.short_description = 'Mark selected as CANCELLED'


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('date', 'doctor', 'is_booked')
    search_fields = ('doctor__username',)
    list_select_related = ('doctor',)
    list_filter = ('is_booked', 'date', 'doctor')
    actions = ['mark_available', 'mark_booked']

    def mark_available(self, request, queryset):
        updated = queryset.update(is_booked=False)
        self.message_user(request, f'{updated} slots marked AVAILABLE.')
    mark_available.short_description = 'Mark selected as AVAILABLE'

    def mark_booked(self, request, queryset):
        updated = queryset.update(is_booked=True)
        self.message_user(request, f'{updated} slots marked BOOKED.')
    mark_booked.short_description = 'Mark selected as BOOKED'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = ('patient__username', 'doctor__username', 'notes')
    list_select_related = ('patient', 'doctor')
    readonly_fields = ('created_at',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'created_at')
    list_filter = ('appointment__created_at',)
    search_fields = ('appointment__id', 'medicines', 'dosage')
    list_select_related = ('appointment',)
    readonly_fields = ('created_at',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'doctor_fee', 'service_charge', 'total', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('appointment__id',)
    readonly_fields = ('total', 'created_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'appointment',
        'method',
        'status',
        'total_amount',
        'transaction_reference',
        'transaction_id',
        'paid_at',
        'verified_at',
        'verified_by',
    )
    list_filter = ('method', 'status', 'paid_at', 'created_at')
    search_fields = (
        'appointment__id',
        'appointment__patient__username',
        'appointment__doctor__username',
        'transaction_reference',
        'transaction_id',
    )
    readonly_fields = ('total_amount', 'created_at', 'verified_at')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'contact', 'email')
    list_filter = ('role',)
    search_fields = ('name', 'email', 'contact')


@admin.register(ReportFile)
class ReportFileAdmin(admin.ModelAdmin):
    list_display = ('patient', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('patient__username',)
    list_select_related = ('patient',)
    readonly_fields = ('uploaded_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'user')
    search_fields = ('user__username', 'message')
    list_select_related = ('user',)
    list_editable = ('is_read',)
    actions = ['mark_read', 'mark_unread']

    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked READ.')
    mark_read.short_description = 'Mark selected as READ'

    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked UNREAD.')
    mark_unread.short_description = 'Mark selected as UNREAD'


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'service_type', 'created_at')
    list_filter = ('service_type', 'created_at')
    search_fields = ('full_name', 'phone_number', 'notes')
    readonly_fields = ('created_at',)


# Integrate Profile with User admin
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def profile_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else 'No Profile'
    profile_role.short_description = 'Role'

admin.site.site_header = 'Hospital Management Admin'
admin.site.site_title = 'Hospital Admin Portal'
admin.site.index_title = 'Welcome to Hospital Admin'
