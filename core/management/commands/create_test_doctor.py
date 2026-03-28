from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import AvailabilitySlot, DoctorProfile, sync_profile_role
from datetime import date, time, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create test doctor and availability slots'

    def handle(self, *args, **options):
        # Create test doctor
        doctor, created = User.objects.get_or_create(
            username='dr.test',
            defaults={
                'first_name': 'Dr. Test',
                'last_name': 'Doctor',
                'email': 'dr.test@hospital.com',
                'is_staff': True,
            }
        )
        password = 'test123'
        doctor.set_password(password)
        doctor.save()
        
        profile, _ = DoctorProfile.objects.get_or_create(
            user=doctor,
            defaults={
                'specialization': 'General Medicine',
                'location': 'Malakpet',
                'experience_years': 8,
                'phone': '+91-9876543210',
                'fee': 500,
            }
        )
        profile.specialization = profile.specialization or 'General Medicine'
        profile.location = profile.location or 'Malakpet'
        profile.experience_years = profile.experience_years or 8
        profile.phone = profile.phone or '+91-9876543210'
        profile.fee = profile.fee or 500
        profile.save()
        sync_profile_role(doctor)
        
        # Create 10 available slots for next 3 days
        tomorrow = date.today() + timedelta(days=1)
        slot_times = [
            (time(10, 0), time(10, 30)),
            (time(11, 0), time(11, 30)), 
            (time(14, 0), time(14, 30)),
            (time(15, 0), time(15, 30)),
        ]
        
        created_slots = 0
        for day_offset in range(3):
            slot_date = tomorrow + timedelta(days=day_offset)
            for start_t, end_t in slot_times:
                slot, _ = AvailabilitySlot.objects.get_or_create(
                    doctor=doctor,
                    date=slot_date,
                    start_time=start_t,
                    end_time=end_t,
                    defaults={'is_booked': False}
                )
                created_slots += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Success! Created doctor "dr.test" (pass: test123) + {created_slots} slots'
            )
        )
        self.stdout.write(self.style.WARNING('Login as dr.test/test123 -> Add more slots via /doctor/availability/'))
