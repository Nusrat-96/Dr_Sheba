from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.urls import reverse_lazy
from allauth.account.views import SignupView
from .forms import PatientSignupForm, DoctorSignupForm
from doctors_app.models import Specialization, Doctor


class LandingPageView(View):
    """Landing page with hero, specializations, featured doctors."""
    template_name = 'landing/index.html'

    def get(self, request):
        specializations = [
            {'name': 'Cardiology', 'icon': 'heart'},
            {'name': 'Dermatology', 'icon': 'skin'},
            {'name': 'Neurology', 'icon': 'brain'},
            {'name': 'Pediatrics', 'icon': 'child'},
            {'name': 'Orthopedics', 'icon': 'bone'},
            {'name': 'Gynecology', 'icon': 'woman'},
            {'name': 'Psychiatry', 'icon': 'mind'},
            {'name': 'General', 'icon': 'med'},
        ]
        featured_doctors = Doctor.objects.filter(is_accepting_patients=True)[:3]
        context = {
            'specializations': specializations,
            'featured_doctors': featured_doctors,
        }
        return render(request, self.template_name, context)


class RoleBasedRedirectView(View):
    """Redirect user based on their role after login."""

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('account_login')

        role = getattr(request.user, 'role', None)
        if role == 'patient':
            return redirect('dashboard:patient')
        elif role == 'doctor':
            return redirect('/dashboard/doctor/')
        elif role == 'admin':
            return redirect('/adminpanel/')
        return redirect('account_login')


class PatientSignupView(SignupView):
    """Patient registration view."""
    form_class = PatientSignupForm
    template_name = 'account/register_patient.html'
    success_url = reverse_lazy('role_redirect')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class DoctorSignupView(SignupView):
    """Doctor registration view."""
    form_class = DoctorSignupForm
    template_name = 'account/register_doctor.html'
    success_url = reverse_lazy('role_redirect')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specializations'] = Specialization.objects.all()
        return context


class RegisterChooseView(View):
    """Landing page to choose registration type."""
    template_name = 'account/register_choose.html'

    def get(self, request):
        return render(request, self.template_name)