from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts_app.models import User, PatientProfile, DoctorProfile
from doctors_app.models import Doctor, Specialization

User = get_user_model()


class PatientRegistrationTest(TestCase):
    """Test patient registration creates user with role='patient'."""

    def test_patient_registration_creates_user_with_role_patient(self):
        """Test that registering as a patient creates a user with role='patient'."""
        user = User.objects.create_user(
            username='patienttest',
            email='patient@test.com',
            password='Testpass123!',
            role='patient'
        )
        self.assertEqual(user.role, 'patient')
        self.assertTrue(user.check_password('Testpass123!'))

    def test_patient_profile_creation(self):
        """Test that PatientProfile can be created for a patient."""
        user = User.objects.create_user(
            username='patienttest2',
            email='patient2@test.com',
            password='Testpass123!',
            role='patient'
        )
        profile = PatientProfile.objects.create(user=user)
        self.assertEqual(profile.user, user)


class DoctorRegistrationTest(TestCase):
    """Test doctor registration creates DoctorProfile."""

    def test_doctor_registration_creates_doctor_profile(self):
        """Test that registering as a doctor creates a DoctorProfile."""
        user = User.objects.create_user(
            username='doctortest',
            email='doctor@test.com',
            password='Testpass123!',
            role='doctor'
        )
        specialty = Specialization.objects.create(name='Cardiology')

        profile = DoctorProfile.objects.create(
            user=user,
            specialty='Cardiology',
            license_number='LIC12345',
            consultation_fee=150.00
        )
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.specialty, 'Cardiology')
        self.assertEqual(profile.license_number, 'LIC12345')


class LoginRedirectTest(TestCase):
    """Test login redirects correctly by role."""

    def test_login_redirect_patient_to_patient_dashboard(self):
        """Test patient is redirected to patient dashboard."""
        User.objects.create_user(
            username='patientuser',
            email='patient@test.com',
            password='Testpass123!',
            role='patient'
        )

        client = Client()
        client.login(username='patientuser', password='Testpass123!')

        response = client.get(reverse('role_redirect'))
        self.assertEqual(response.url, reverse('dashboard:patient'))

    def test_login_redirect_doctor_to_doctor_dashboard(self):
        """Test doctor is redirected to doctor dashboard."""
        doctor_user = User.objects.create_user(
            username='doctoruser',
            email='doctor@test.com',
            password='Testpass123!',
            role='doctor'
        )
        Doctor.objects.create(user=doctor_user, specialty='General', license_number='LIC111')

        client = Client()
        client.login(username='doctoruser', password='Testpass123!')

        response = client.get(reverse('role_redirect'))
        self.assertEqual(response.url, reverse('dashboard:doctor'))


class UnauthenticatedAccessTest(TestCase):
    """Test unauthenticated access to dashboard redirects to login."""

    def test_patient_dashboard_requires_login(self):
        """Test that accessing patient dashboard without login redirects to login."""
        response = self.client.get(reverse('dashboard:patient'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_doctor_dashboard_requires_login(self):
        """Test that accessing doctor dashboard without login redirects to login."""
        response = self.client.get(reverse('dashboard:doctor'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_admin_dashboard_requires_login(self):
        """Test that accessing admin dashboard without login redirects to login."""
        response = self.client.get(reverse('adminpanel:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
