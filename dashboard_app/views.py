from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from functools import wraps

from appointments_app.models import Appointment, TimeSlot
from doctors_app.models import Doctor


def role_required(required_role):
    """Decorator to restrict access to users with a specific role."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            if request.user.role != required_role:
                messages.error(request, f"Access denied. This page is for {required_role}s only.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class PatientDashboardView(LoginRequiredMixin, View):
    """Patient dashboard with appointments overview."""
    template_name = 'dashboard/patient.html'

    def get(self, request):
        if request.user.role != 'patient':
            messages.error(request, "Access denied. This page is for patients only.")
            return redirect('home')

        today = timezone.now().date()

        # Upcoming appointments (confirmed, date >= today)
        upcoming_appointments = Appointment.objects.filter(
            patient=request.user,
            status='confirmed',
            time_slot__date__gte=today
        ).select_related('doctor', 'doctor__user', 'time_slot').order_by('time_slot__date', 'time_slot__start_time')

        # Past appointments (completed)
        past_appointments = Appointment.objects.filter(
            patient=request.user,
            status='completed'
        ).select_related('doctor', 'doctor__user', 'time_slot').order_by('-time_slot__date')[:5]

        # Cancelled count
        cancelled_count = Appointment.objects.filter(
            patient=request.user,
            status='cancelled'
        ).count()

        # Upcoming count
        upcoming_count = upcoming_appointments.count()

        # Completed count
        completed_count = Appointment.objects.filter(
            patient=request.user,
            status='completed'
        ).count()

        context = {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'upcoming_count': upcoming_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
        }
        return render(request, self.template_name, context)


class DoctorDashboardView(LoginRequiredMixin, View):
    """Doctor dashboard with schedule and appointments overview."""
    template_name = 'dashboard/doctor.html'

    def get(self, request):
        if request.user.role != 'doctor':
            messages.error(request, "Access denied. This page is for doctors only.")
            return redirect('home')

        doctor = get_object_or_404(Doctor, user=request.user)
        today = timezone.now().date()

        # Today's confirmed appointments
        today_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='confirmed',
            time_slot__date=today
        ).select_related('patient', 'time_slot').order_by('time_slot__start_time')

        # Pending appointment requests
        pending_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='pending'
        ).select_related('patient', 'time_slot').order_by('time_slot__date', 'time_slot__start_time')

        # Total unique patients
        total_patients = Appointment.objects.filter(
            doctor=doctor
        ).values('patient').distinct().count()

        context = {
            'today_appointments': today_appointments,
            'pending_appointments': pending_appointments,
            'total_patients': total_patients,
            'doctor': doctor,
        }
        return render(request, self.template_name, context)


class DoctorScheduleView(LoginRequiredMixin, View):
    """Doctor manages their time slots."""
    template_name = 'dashboard/schedule.html'

    def get(self, request):
        if request.user.role != 'doctor':
            messages.error(request, "Access denied. This page is for doctors only.")
            return redirect('home')

        doctor = get_object_or_404(Doctor, user=request.user)
        today = timezone.now().date()

        # Get time slots for next 30 days
        end_date = today + timedelta(days=30)
        time_slots = TimeSlot.objects.filter(
            doctor=doctor,
            date__gte=today,
            date__lt=end_date
        ).order_by('date', 'start_time')

        context = {
            'time_slots': time_slots,
            'doctor': doctor,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Add a new time slot or delete a slot (via _method)."""
        if request.user.role != 'doctor':
            messages.error(request, "Access denied. This page is for doctors only.")
            return redirect('home')

        doctor = get_object_or_404(Doctor, user=request.user)

        # Check if this is a delete request
        if request.POST.get('_method') == 'DELETE':
            return self._delete_slot(request, doctor)

        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')

        if not date_str or not start_time_str or not end_time_str:
            messages.error(request, "Please provide date, start time, and end time.")
            return redirect('dashboard:schedule')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Check if date is not in the past
            if date < timezone.now().date():
                messages.error(request, "Cannot create slots in the past.")
                return redirect('dashboard:schedule')

            # Create the time slot
            time_slot = TimeSlot.objects.create(
                doctor=doctor,
                date=date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            messages.success(request, f"Time slot added for {date} at {start_time}.")
        except ValueError:
            messages.error(request, "Invalid date or time format.")

        return redirect('dashboard:schedule')

    def _delete_slot(self, request, doctor):
        """Delete a time slot."""
        slot_id = request.POST.get('slot_id')

        if not slot_id:
            messages.error(request, "Slot ID is required.")
            return redirect('dashboard:schedule')

        time_slot = get_object_or_404(TimeSlot, pk=slot_id, doctor=doctor)

        # Check if slot has an appointment
        if time_slot.appointments.exists():
            messages.error(request, "Cannot delete a slot with existing appointments.")
        else:
            time_slot.delete()
            messages.success(request, "Time slot removed.")

        return redirect('dashboard:schedule')
