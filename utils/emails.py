from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone


def send_appointment_confirmation(appointment):
    """Send appointment confirmation email to patient."""
    subject = f"Appointment Confirmed - Dr. {appointment.doctor.user.get_full_name()}"

    context = {
        'patient_name': appointment.patient.get_full_name() or appointment.patient.username,
        'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}",
        'date': appointment.time_slot.date,
        'start_time': appointment.time_slot.start_time,
        'end_time': appointment.time_slot.end_time,
        'clinic_name': appointment.doctor.clinic_name or "Dr. Sheba Clinic",
        'specializations': appointment.doctor.specializations.all(),
    }

    text_content = f"""
Dear {context['patient_name']},

Your appointment has been confirmed!

Doctor: {context['doctor_name']}
Date: {context['date']}
Time: {context['start_time']} - {context['end_time']}
Clinic: {context['clinic_name']}

Please arrive 15 minutes before your scheduled time.

Thank you for choosing Dr. Sheba!
"""

    html_content = render_to_string('emails/appointment_confirmation.html', context)

    return _send_email(subject, text_content, html_content, [appointment.patient.email])


def send_appointment_reminder(appointment):
    """Send appointment reminder email 24 hours before appointment."""
    subject = f"Appointment Reminder - Dr. {appointment.doctor.user.get_full_name()} tomorrow"

    context = {
        'patient_name': appointment.patient.get_full_name() or appointment.patient.username,
        'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}",
        'date': appointment.time_slot.date,
        'start_time': appointment.time_slot.start_time,
        'end_time': appointment.time_slot.end_time,
        'clinic_name': appointment.doctor.clinic_name or "Dr. Sheba Clinic",
    }

    text_content = f"""
Dear {context['patient_name']},

This is a reminder that you have an appointment tomorrow!

Doctor: {context['doctor_name']}
Date: {context['date']}
Time: {context['start_time']} - {context['end_time']}
Clinic: {context['clinic_name']}

Please arrive 15 minutes early.

See you soon!
"""

    html_content = render_to_string('emails/appointment_reminder.html', context)

    return _send_email(subject, text_content, html_content, [appointment.patient.email])


def send_doctor_approval_email(doctor):
    """Notify doctor their account has been approved."""
    subject = "Your Dr. Sheba Account Has Been Approved!"

    context = {
        'doctor_name': f"Dr. {doctor.user.get_full_name()}",
        'specializations': doctor.specializations.all(),
        'consultation_fee': doctor.consultation_fee,
    }

    text_content = f"""
Dear {context['doctor_name']},

Congratulations! Your registration with Dr. Sheba has been approved.

You can now:
- Set up your availability and time slots
- Accept appointment requests from patients
- View and manage your appointments

Please log in to your dashboard to get started.

Best regards,
Dr. Sheba Team
"""

    html_content = render_to_string('emails/doctor_approved.html', context)

    return _send_email(subject, text_content, html_content, [doctor.user.email])


def send_appointment_status_update(appointment):
    """Notify patient when doctor confirms or cancels an appointment."""
    status_messages = {
        'confirmed': {
            'subject': f"Appointment Confirmed - Dr. {appointment.doctor.user.get_full_name()}",
            'message': "Your appointment has been confirmed by the doctor.",
        },
        'cancelled': {
            'subject': f"Appointment Cancelled - Dr. {appointment.doctor.user.get_full_name()}",
            'message': "Your appointment has been cancelled.",
        },
    }

    status_info = status_messages.get(appointment.status, {
        'subject': f"Appointment Update - Dr. {appointment.doctor.user.get_full_name()}",
        'message': "Your appointment status has been updated.",
    })

    context = {
        'patient_name': appointment.patient.get_full_name() or appointment.patient.username,
        'doctor_name': f"Dr. {appointment.doctor.user.get_full_name()}",
        'date': appointment.time_slot.date,
        'start_time': appointment.time_slot.start_time,
        'end_time': appointment.time_slot.end_time,
        'status': appointment.status,
        'status_display': appointment.get_status_display(),
        'message': status_info['message'],
        'clinic_name': appointment.doctor.clinic_name or "Dr. Sheba Clinic",
    }

    text_content = f"""
Dear {context['patient_name']},

{context['message']}

Doctor: {context['doctor_name']}
Date: {context['date']}
Time: {context['start_time']} - {context['end_time']}

{"Please remember to arrive 15 minutes early." if appointment.status == "confirmed" else ""}

Best regards,
Dr. Sheba Team
"""

    html_content = render_to_string('emails/status_update.html', context)

    return _send_email(status_info['subject'], text_content, html_content, [appointment.patient.email])


def _send_email(subject, text_content, html_content, recipient_list):
    """Helper to send HTML email."""
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception:
        return False
