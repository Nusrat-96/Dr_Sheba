from django.db import models
from django.conf import settings


class Specialization(models.Model):
    """Medical specializations (e.g., Cardiology, Dermatology)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Specializations"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Doctor listing with profile and availability."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor')
    specializations = models.ManyToManyField(Specialization, related_name='doctors')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    available_days = models.JSONField(default=list)
    available_time_start = models.TimeField(null=True, blank=True)
    available_time_end = models.TimeField(null=True, blank=True)
    is_accepting_patients = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"


class DoctorReview(models.Model):
    """Patient reviews for doctors."""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.patient.username} for Dr. {self.doctor.user.username}"
