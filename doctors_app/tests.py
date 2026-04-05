from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts_app.models import User
from doctors_app.models import Doctor, Specialization

User = get_user_model()


class DoctorListingTest(TestCase):
    """Test doctor listing functionality."""

    def setUp(self):
        self.client = Client()

        # Create specialization
        self.cardiology = Specialization.objects.create(name='Cardiology')
        self.dermatology = Specialization.objects.create(name='Dermatology')

        # Create approved doctor
        self.approved_doctor_user = User.objects.create_user(
            username='approved_doctor',
            email='approved@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.approved_doctor = Doctor.objects.create(
            user=self.approved_doctor_user,
            specialty='Cardiology',
            license_number='LIC123',
            consultation_fee=150.00,
            is_verified=True,
            is_accepting_patients=True
        )
        self.approved_doctor.specializations.add(self.cardiology)

        # Create unapproved doctor
        self.unapproved_doctor_user = User.objects.create_user(
            username='unapproved_doctor',
            email='unapproved@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.unapproved_doctor = Doctor.objects.create(
            user=self.unapproved_doctor_user,
            specialty='Dermatology',
            license_number='LIC456',
            consultation_fee=100.00,
            is_verified=False,
            is_accepting_patients=True
        )
        self.unapproved_doctor.specializations.add(self.dermatology)

    def test_doctor_listing_returns_only_approved_doctors(self):
        """Test doctor listing returns only approved doctors."""
        response = self.client.get(reverse('doctors:list'))

        self.assertEqual(response.status_code, 200)
        doctors = response.context['doctors']
        self.assertEqual(doctors.count(), 1)
        self.assertEqual(doctors.first(), self.approved_doctor)

    def test_unapproved_doctor_not_shown_in_listing(self):
        """Test unapproved doctor is not shown in listing."""
        response = self.client.get(reverse('doctors:list'))

        doctors = response.context['doctors']
        self.assertNotIn(self.unapproved_doctor, doctors)


class SpecializationFilterTest(TestCase):
    """Test specialization filter functionality."""

    def setUp(self):
        self.client = Client()

        # Create specializations
        self.cardiology = Specialization.objects.create(name='Cardiology')
        self.dermatology = Specialization.objects.create(name='Dermatology')

        # Create doctors
        self.doctor1_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.doctor1 = Doctor.objects.create(
            user=self.doctor1_user,
            specialty='Cardiology',
            license_number='LIC111',
            consultation_fee=150.00,
            is_verified=True,
            is_accepting_patients=True
        )
        self.doctor1.specializations.add(self.cardiology)

        self.doctor2_user = User.objects.create_user(
            username='doctor2',
            email='doctor2@test.com',
            password='Testpass123!',
            role='doctor'
        )
        self.doctor2 = Doctor.objects.create(
            user=self.doctor2_user,
            specialty='Dermatology',
            license_number='LIC222',
            consultation_fee=100.00,
            is_verified=True,
            is_accepting_patients=True
        )
        self.doctor2.specializations.add(self.dermatology)

    def test_specialization_filter_works_correctly(self):
        """Test that filtering by specialization works correctly."""
        response = self.client.get(reverse('doctors:list'), {'specialization': self.cardiology.id})

        doctors = response.context['doctors']
        self.assertEqual(doctors.count(), 1)
        self.assertEqual(doctors.first(), self.doctor1)

    def test_search_by_doctor_name(self):
        """Test searching doctors by name."""
        response = self.client.get(reverse('doctors:search'), {'q': 'doctor1'})

        doctors = response.context['doctors']
        self.assertEqual(doctors.count(), 1)
        self.assertEqual(doctors.first(), self.doctor1)
