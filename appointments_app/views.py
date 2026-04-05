from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from .models import Appointment, TimeSlot
from doctors_app.models import Doctor


class BookAppointmentView(LoginRequiredMixin, View):
    """Book an appointment - patient only."""
    template_name = 'appointments/book.html'

    def get(self, request, doctor_id):
        # Only patients can book
        if request.user.role != 'patient':
            messages.error(request, "Only patients can book appointments.")
            return redirect('home')

        doctor = get_object_or_404(
            Doctor.objects.select_related('user').prefetch_related('specializations'),
            pk=doctor_id,
            is_accepting_patients=True
        )

        # Get available time slots for next 7 days
        today = timezone.now().date()
        end_date = today + timedelta(days=7)

        time_slots = TimeSlot.objects.filter(
            doctor=doctor,
            date__gte=today,
            date__lt=end_date,
            is_available=True
        ).order_by('date', 'start_time')

        # Group slots by date
        slots_by_date = {}
        for slot in time_slots:
            date_str = slot.date.strftime('%Y-%m-%d')
            if date_str not in slots_by_date:
                slots_by_date[date_str] = {
                    'date': slot.date,
                    'slots': []
                }
            slots_by_date[date_str]['slots'].append(slot)

        context = {
            'doctor': doctor,
            'slots_by_date': slots_by_date,
        }
        return render(request, self.template_name, context)

    def post(self, request, doctor_id):
        if request.user.role != 'patient':
            messages.error(request, "Only patients can book appointments.")
            return redirect('home')

        doctor = get_object_or_404(Doctor, pk=doctor_id, is_accepting_patients=True)
        slot_id = request.POST.get('time_slot_id')
        reason = request.POST.get('reason', '')

        if not slot_id:
            messages.error(request, "Please select a time slot.")
            return redirect('appointments:book', doctor_id=doctor_id)

        time_slot = get_object_or_404(TimeSlot, pk=slot_id, doctor=doctor, is_available=True)

        # Create appointment
        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            time_slot=time_slot,
            status='pending',
            reason=reason
        )

        # Mark slot as unavailable
        time_slot.is_available = False
        time_slot.save()

        # Send confirmation email
        try:
            send_mail(
                subject='Appointment Confirmed - Dr. Sheba',
                message=f"""Dear {request.user.get_full_name()},

Your appointment has been booked successfully!

Doctor: Dr. {doctor.user.get_full_name()}
Date: {time_slot.date}
Time: {time_slot.start_time} - {time_slot.end_time}

Please arrive 15 minutes before your scheduled time.

Thank you for using Dr. Sheba!""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Email failure shouldn't block booking

        messages.success(request, "Appointment booked successfully!")
        return redirect('appointments:detail', pk=appointment.pk)


class CancelAppointmentView(LoginRequiredMixin, View):
    """Cancel an appointment - patient only, if >2 hours before slot."""

    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)

        # Check if cancellation is allowed (>2 hours before slot)
        slot_time = datetime.combine(appointment.time_slot.date, appointment.time_slot.start_time)
        if timezone.is_naive(slot_time):
            slot_time = timezone.make_aware(slot_time)

        if slot_time < timezone.now() + timedelta(hours=2):
            messages.error(request, "Cannot cancel within 2 hours of appointment time.")
            return redirect('appointments:detail', pk=pk)

        # Check if already cancelled
        if appointment.status == 'cancelled':
            messages.error(request, "Appointment is already cancelled.")
            return redirect('appointments:detail', pk=pk)

        # Cancel appointment and free up slot
        appointment.status = 'cancelled'
        appointment.save()

        appointment.time_slot.is_available = True
        appointment.time_slot.save()

        messages.success(request, "Appointment cancelled successfully.")
        return redirect('appointments:detail', pk=pk)


class ConfirmAppointmentView(LoginRequiredMixin, View):
    """Confirm a pending appointment - doctor only."""

    def post(self, request, pk):
        if request.user.role != 'doctor':
            messages.error(request, "Only doctors can confirm appointments.")
            return redirect('home')

        appointment = get_object_or_404(
            Appointment,
            pk=pk,
            doctor__user=request.user,
            status='pending'
        )

        appointment.status = 'confirmed'
        appointment.save()

        # Send email to patient
        try:
            send_mail(
                subject='Appointment Confirmed by Doctor - Dr. Sheba',
                message=f"""Dear {appointment.patient.get_full_name()},

Your appointment has been CONFIRMED by Dr. {appointment.doctor.user.get_full_name()}.

Date: {appointment.time_slot.date}
Time: {appointment.time_slot.start_time} - {appointment.time_slot.end_time}

Please arrive 15 minutes before your scheduled time.

Thank you!""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, "Appointment confirmed!")
        return redirect('appointments:detail', pk=pk)


class AppointmentDetailView(LoginRequiredMixin, View):
    """Show appointment details."""
    template_name = 'appointments/detail.html'

    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)

        # Check access permission
        if (request.user != appointment.patient and
            request.user != appointment.doctor.user and
            request.user.role != 'admin'):
            messages.error(request, "You don't have permission to view this appointment.")
            return redirect('home')

        context = {
            'appointment': appointment,
            'can_cancel': False,
            'can_confirm': False,
        }

        # Check if patient can cancel (>2 hours before slot)
        if appointment.patient == request.user and appointment.status in ['pending', 'confirmed']:
            slot_time = datetime.combine(appointment.time_slot.date, appointment.time_slot.start_time)
            if timezone.is_naive(slot_time):
                slot_time = timezone.make_aware(slot_time)
            if slot_time >= timezone.now() + timedelta(hours=2):
                context['can_cancel'] = True

        # Check if doctor can confirm
        if (appointment.doctor.user == request.user and
            appointment.status == 'pending'):
            context['can_confirm'] = True

        return render(request, self.template_name, context)