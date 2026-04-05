from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.db.models import Q

from django.db import models
from accounts_app.models import User
from doctors_app.models import Doctor, Specialization
from appointments_app.models import Appointment, TimeSlot


def staff_required(view_func):
    """Decorator to require admin/staff status."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, "Access denied. Admin only.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


class BaseAdminView(LoginRequiredMixin, View):
    """Base view with staff check."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.error(request, "Access denied. Admin only.")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(BaseAdminView):
    """Admin dashboard with overview statistics."""
    template_name = 'adminpanel/dashboard.html'

    def get(self, request):
        today = timezone.now().date()

        # Stats
        total_doctors = Doctor.objects.count()
        total_patients = User.objects.filter(role='patient').count()
        total_appointments_today = Appointment.objects.filter(
            time_slot__date=today
        ).count()

        # Pending doctor approvals (doctors who are not verified)
        pending_doctors = Doctor.objects.filter(is_verified=False).select_related('user')

        # Recent appointments
        recent_appointments = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'patient', 'time_slot'
        ).order_by('-created_at')[:10]

        context = {
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_appointments_today': total_appointments_today,
            'pending_doctors': pending_doctors,
            'pending_count': pending_doctors.count(),
            'recent_appointments': recent_appointments,
        }
        return render(request, self.template_name, context)


class AllAppointmentsView(BaseAdminView):
    """View all appointments with filters."""
    template_name = 'adminpanel/appointments.html'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')

        appointments = Appointment.objects.select_related(
            'doctor', 'doctor__user', 'patient', 'time_slot'
        ).order_by('-created_at')

        if status_filter:
            appointments = appointments.filter(status=status_filter)

        if date_filter:
            appointments = appointments.filter(time_slot__date=date_filter)

        context = {
            'appointments': appointments,
            'status_filter': status_filter,
            'date_filter': date_filter,
            'status_choices': Appointment.STATUS_CHOICES,
        }
        return render(request, self.template_name, context)


class AllUsersView(BaseAdminView):
    """View all users with role filter."""
    template_name = 'adminpanel/users.html'

    def get(self, request):
        role_filter = request.GET.get('role', '')

        users = User.objects.annotate(
            appointment_count=models.Count('appointments')
        ).order_by('-date_joined')

        if role_filter:
            users = users.filter(role=role_filter)

        context = {
            'users': users,
            'role_filter': role_filter,
        }
        return render(request, self.template_name, context)


class ApproveDoctorView(BaseAdminView):
    """Approve a doctor registration."""

    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        doctor.is_verified = True
        doctor.save()

        # Send approval email
        try:
            send_mail(
                subject='Your Dr. Sheba Account Has Been Approved',
                message=f"""Dear Dr. {doctor.user.get_full_name()},

                            Congratulations! Your registration with Dr. Sheba has been approved.

                            You can now log in and start accepting patients.

                            Best regards,
                            Dr. Sheba Team""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[doctor.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, f"Dr. {doctor.user.get_full_name()} has been approved.")
        return redirect('adminpanel:dashboard')


class RejectDoctorView(BaseAdminView):
    """Reject/delete a doctor registration."""

    def post(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        doctor_user = doctor.user
        doctor_email = doctor_user.email
        doctor_name = doctor_user.get_full_name()
        rejection_reason = request.POST.get('reason', 'Your application did not meet our requirements.')

        doctor.delete()

        # Send rejection email with reason
        try:
            send_mail(
                subject='Your Dr. Sheba Application Status',
                message=f"""Dear {doctor_name},

Thank you for applying to join Dr. Sheba.

Unfortunately, we are unable to approve your application at this time.
Reason: {rejection_reason}

If you have any questions, please contact our support team.

Best regards,
Dr. Sheba Team""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[doctor_email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, f"Registration for {doctor_name} has been rejected.")
        return redirect('adminpanel:dashboard')
