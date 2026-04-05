from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from accounts_app.models import User
from doctors_app.models import Doctor, Specialization
from appointments_app.models import Appointment, TimeSlot

User = get_user_model()


class BookAppointmentTest(TestCase):
    """Test appointment booking functionality."""

    def setUp(self):
        self.client = Client()

        # Create specialization
        self.specialization = Specialization.objects.create(name='Cardiology')

        # Create doctor user and profile
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='Cardiology',
            license_number='LIC123',
            consultation_fee=150.00,
            is_verified=True
        )
        self.doctor.specializations.add(self.specialization)

        # Create patient
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='Testpass123!',
            role='patient'
        )

        # Create time slot (tomorrow)
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.time_slot = TimeSlot.objects.create(
            doctor=self.doctor,
            date=tomorrow,
            start_time=datetime.strptime('09:00', '%H:%M').time(),
            end_time=datetime.strptime('09:30', '%H:%M').time(),
            is_available=True
        )

    def test_booking_appointment_marks_slot_unavailable(self):
        """Test booking an appointment marks the slot as unavailable."""
        self.client.login(username='patient', password='Testpass123!')

        response = self.client.post(reverse('appointments:book', kwargs={'doctor_id': self.doctor.id}), {
            'time_slot_id': self.time_slot.id,
            'reason': 'Checkup',
        })

        # Slot should be unavailable
        self.time_slot.refresh_from_db()
        self.assertFalse(self.time_slot.is_available)

        # Appointment should be created
        self.assertEqual(Appointment.objects.count(), 1)

    def test_patient_cannot_book_already_booked_slot(self):
        """Test patient cannot book an already-booked slot."""
        # Book the slot first
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            time_slot=self.time_slot,
            status='pending'
        )
        self.time_slot.is_available = False
        self.time_slot.save()

        # Create another patient
        patient2 = User.objects.create_user(
            username='patient2',
            email='patient2@test.com',
            password='Testpass123!',
            role='patient'
        )
        self.client.login(username='patient2', password='Testpass123!')

        # Try to book same slot
        response = self.client.post(reverse('appointments:book', kwargs={'doctor_id': self.doctor.id}), {
            'time_slot_id': self.time_slot.id,
            'reason': 'Checkup',
        })

        # Should redirect with error, no new appointment created
        self.assertEqual(Appointment.objects.filter(patient=patient2).count(), 0)


class CancelAppointmentTest(TestCase):
    """Test appointment cancellation."""

    def setUp(self):
        self.client = Client()

        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='General',
            license_number='LIC123',
            consultation_fee=100.00,
            is_verified=True
        )

        # Create patient
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='Testpass123!',
            role='patient'
        )

    def test_cancellation_only_works_if_more_than_2_hours_before_slot(self):
        """Test cancellation only works if >2 hours before slot."""
        # Create a slot in 1 hour (less than 2 hours)
        soon = timezone.now() + timedelta(hours=1)
        slot = TimeSlot.objects.create(
            doctor=self.doctor,
            date=soon.date(),
            start_time=soon.time(),
            end_time=(soon + timedelta(minutes=30)).time(),
            is_available=False
        )

        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            time_slot=slot,
            status='confirmed'
        )

        self.client.login(username='patient', password='Testpass123!')

        response = self.client.post(reverse('appointments:cancel', kwargs={'pk': appointment.pk}))

        # Should not cancel
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'confirmed')

    def test_cancellation_works_if_more_than_2_hours_before_slot(self):
        """Test cancellation works if >2 hours before slot."""
        # Create a slot in 3 hours (more than 2 hours)
        later = timezone.now() + timedelta(hours=3)
        slot = TimeSlot.objects.create(
            doctor=self.doctor,
            date=later.date(),
            start_time=later.time(),
            end_time=(later + timedelta(minutes=30)).time(),
            is_available=False
        )

        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            time_slot=slot,
            status='confirmed'
        )

        self.client.login(username='patient', password='Testpass123!')

        response = self.client.post(reverse('appointments:cancel', kwargs={'pk': appointment.pk}))

        # Should cancel
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')

        # Slot should be available again
        slot.refresh_from_db()
        self.assertTrue(slot.is_available)


class ConfirmAppointmentTest(TestCase):
    """Test appointment confirmation by doctor."""

    def setUp(self):
        self.client = Client()

        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialty='General',
            license_number='LIC123',
            consultation_fee=100.00,
            is_verified=True
        )

        # Create patient
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='Testpass123!',
            role='patient'
        )

        # Create time slot
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.time_slot = TimeSlot.objects.create(
            doctor=self.doctor,
            date=tomorrow,
            start_time=datetime.strptime('10:00', '%H:%M').time(),
            end_time=datetime.strptime('10:30', '%H:%M').time(),
            is_available=False
        )

        # Create pending appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            time_slot=self.time_slot,
            status='pending'
        )

    def test_doctor_can_confirm_pending_appointment(self):
        """Test doctor can confirm a pending appointment."""
        self.client.login(username='doctor', password='Testpass123!')

        response = self.client.post(reverse('appointments:confirm', kwargs={'pk': self.appointment.pk}))

        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')

    def test_patient_cannot_confirm_appointment(self):
        """Test that patients cannot confirm appointments."""
        self.client.login(username='patient', password='Testpass123!')

        response = self.client.post(reverse('appointments:confirm', kwargs={'pk': self.appointment.pk}))

        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'pending')
