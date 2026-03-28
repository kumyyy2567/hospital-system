from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import AvailabilitySlot, DoctorProfile, sync_profile_role


DOCTOR_SEED_DATA = [
    {
        'username': 'dr.meera',
        'first_name': 'Meera',
        'last_name': 'Reddy',
        'email': 'dr.meera@hospital.com',
        'specialization': 'Cardiology',
        'location': 'Malakpet',
        'experience_years': 12,
        'phone': '+91-9000001111',
        'fee': 900,
    },
    {
        'username': 'dr.arjun',
        'first_name': 'Arjun',
        'last_name': 'Varma',
        'email': 'dr.arjun@hospital.com',
        'specialization': 'Neurology',
        'location': 'Secunderabad',
        'experience_years': 15,
        'phone': '+91-9000002222',
        'fee': 1200,
    },
    {
        'username': 'dr.sneha',
        'first_name': 'Sneha',
        'last_name': 'Nair',
        'email': 'dr.sneha@hospital.com',
        'specialization': 'Pediatrics',
        'location': 'Hitec City',
        'experience_years': 9,
        'phone': '+91-9000003333',
        'fee': 750,
    },
    {
        'username': 'dr.raghav',
        'first_name': 'Raghav',
        'last_name': 'Sharma',
        'email': 'dr.raghav@hospital.com',
        'specialization': 'Orthopedic',
        'location': 'Somajiguda',
        'experience_years': 11,
        'phone': '+91-9000004444',
        'fee': 850,
    },
    {
        'username': 'dr.farah',
        'first_name': 'Farah',
        'last_name': 'Khan',
        'email': 'dr.farah@hospital.com',
        'specialization': 'Oncology',
        'location': 'Malakpet',
        'experience_years': 14,
        'phone': '+91-9000005555',
        'fee': 1400,
    },
    {
        'username': 'dr.vikram',
        'first_name': 'Vikram',
        'last_name': 'Iyer',
        'email': 'dr.vikram@hospital.com',
        'specialization': 'Gastroenterology',
        'location': 'Hitec City',
        'experience_years': 13,
        'phone': '+91-9000006666',
        'fee': 980,
    },
]

SLOT_TIMESETS = [
    [(time(9, 30), time(10, 0)), (time(10, 15), time(10, 45)), (time(17, 0), time(17, 30))],
    [(time(10, 0), time(10, 30)), (time(11, 15), time(11, 45)), (time(15, 0), time(15, 30))],
    [(time(9, 0), time(9, 30)), (time(13, 0), time(13, 30)), (time(18, 0), time(18, 30))],
    [(time(8, 45), time(9, 15)), (time(12, 30), time(13, 0)), (time(16, 15), time(16, 45))],
]


class Command(BaseCommand):
    help = 'Seed multiple demo doctors with realistic hospital locations and live slots'

    def handle(self, *args, **options):
        created_doctors = 0
        created_slots = 0
        password = 'doctor123'
        tomorrow = date.today() + timedelta(days=1)

        for index, payload in enumerate(DOCTOR_SEED_DATA):
            doctor, user_created = User.objects.get_or_create(
                username=payload['username'],
                defaults={
                    'first_name': payload['first_name'],
                    'last_name': payload['last_name'],
                    'email': payload['email'],
                    'is_staff': True,
                },
            )
            if user_created:
                created_doctors += 1

            doctor.first_name = payload['first_name']
            doctor.last_name = payload['last_name']
            doctor.email = payload['email']
            doctor.is_staff = True
            doctor.set_password(password)
            doctor.save()

            profile, _ = DoctorProfile.objects.get_or_create(user=doctor)
            profile.specialization = payload['specialization']
            profile.location = payload['location']
            profile.experience_years = payload['experience_years']
            profile.phone = payload['phone']
            profile.fee = payload['fee']
            profile.save()
            sync_profile_role(doctor)

            slot_times = SLOT_TIMESETS[index % len(SLOT_TIMESETS)]
            for day_offset in range(5):
                slot_date = tomorrow + timedelta(days=day_offset)
                for start_t, end_t in slot_times:
                    _, slot_created = AvailabilitySlot.objects.get_or_create(
                        doctor=doctor,
                        date=slot_date,
                        start_time=start_t,
                        end_time=end_t,
                        defaults={'is_booked': False},
                    )
                    if slot_created:
                        created_slots += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded demo doctor roster. New doctors: {created_doctors}, new slots: {created_slots}.'
            )
        )
        self.stdout.write(self.style.WARNING('Demo doctor password for all seeded accounts: doctor123'))
