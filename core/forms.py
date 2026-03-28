from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    PatientProfile,
    DoctorProfile,
    AvailabilitySlot,
    Appointment,
    Payment,
    PAYMENT_METHOD_CHOICES,
    MedicalRecord,
    Prescription,
    Invoice,
    Staff,
    ReportFile,
    CallbackRequest,
)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['age', 'gender', 'contact', 'medical_history']


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'location', 'experience_years', 'phone', 'fee']


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ['date', 'start_time', 'end_time']


class AppointmentForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label='Payment Method',
        initial='UPI',
        widget=forms.Select(attrs={'class': 'form-control', 'data-booking-payment-select': 'true'}),
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'slot', 'gmail']
        labels = {
            'doctor': 'Doctor',
            'slot': 'Appointment Slot',
            'gmail': 'Confirmation Email',
        }
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control', 'data-booking-doctor-select': 'true'}),
            'slot': forms.Select(attrs={'class': 'form-control', 'data-booking-slot-select': 'true'}),
            'gmail': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'name@example.com',
                    'autocomplete': 'email',
                    'inputmode': 'email',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        doctor_queryset = kwargs.pop('doctor_queryset', User.objects.none())
        slot_queryset = kwargs.pop('slot_queryset', AvailabilitySlot.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = doctor_queryset
        self.fields['slot'].queryset = slot_queryset
        self.fields['doctor'].empty_label = 'Select a doctor'
        self.fields['slot'].empty_label = 'Select a slot'
        self.fields['payment_method'].initial = self.initial.get('payment_method', 'UPI')

    def clean_gmail(self):
        gmail = self.cleaned_data.get('gmail', '')
        if '@' not in gmail or '.' not in gmail.split('@')[-1]:
            raise forms.ValidationError('Please enter a valid email address.')
        return gmail

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        slot = cleaned.get('slot')
        if doctor and slot and slot.doctor != doctor:
            raise forms.ValidationError('Selected slot does not belong to the chosen doctor.')
        return cleaned


class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['transaction_id', 'proof_file', 'submitted_note']
        labels = {
            'transaction_id': 'Transaction ID / UTR Number',
            'proof_file': 'Payment Screenshot',
            'submitted_note': 'Payment Note',
        }
        widgets = {
            'transaction_id': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter UTR, reference, or transaction ID',
                    'autocomplete': 'off',
                }
            ),
            'submitted_note': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Optional note for the admin team',
                }
            ),
            'proof_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id', '').strip()
        if len(transaction_id) < 6:
            raise forms.ValidationError('Enter a valid transaction ID or UTR number.')
        return transaction_id

    def clean(self):
        cleaned = super().clean()
        proof_file = cleaned.get('proof_file')
        if not proof_file and not getattr(self.instance, 'proof_file', None):
            self.add_error('proof_file', 'Upload a payment screenshot before submitting for verification.')
        return cleaned


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['notes']


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medicines', 'dosage', 'notes']


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['doctor_fee', 'service_charge']


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'role', 'contact', 'email']


class ReportUploadForm(forms.ModelForm):
    class Meta:
        model = ReportFile
        fields = ['file']


class CallbackRequestForm(forms.ModelForm):
    class Meta:
        model = CallbackRequest
        fields = ['full_name', 'phone_number', 'service_type', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us what support you need'}),
        }

    def clean_phone_number(self):
        phone_number = ''.join(char for char in self.cleaned_data.get('phone_number', '') if char.isdigit())
        if len(phone_number) < 10:
            raise forms.ValidationError('Enter a valid phone number.')
        return phone_number
