from django.contrib import admin
from django.utils.html import format_html
from .models import Doctor, Specialization, DoctorReview


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'doctor_count')
    search_fields = ('name',)

    def doctor_count(self, obj):
        return obj.doctors.count()
    doctor_count.short_description = 'Doctors'


class DoctorInline(admin.TabularInline):
    model = Doctor.specializations.through
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'user_name', 'specializations_list', 'clinic_name',
        'consultation_fee', 'years_of_experience', 'is_accepting_patients', 'is_verified_badge', 'rating_display'
    )
    list_filter = ('is_accepting_patients', 'specializations', 'years_of_experience')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'clinic_name', 'bio')
    list_per_page = 25

    fieldsets = (
        ('User & Profile', {
            'fields': ('user', 'specializations', 'bio')
        }),
        ('Professional Info', {
            'fields': ('education', 'languages', 'location', 'clinic_name', 'years_of_experience')
        }),
        ('Availability', {
            'fields': ('available_days', 'available_time_start', 'available_time_end', 'is_accepting_patients')
        }),
        ('Billing', {
            'fields': ('consultation_fee',)
        }),
        ('Stats (Auto-calculated)', {
            'fields': ('rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('rating', 'total_reviews')

    def user_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"
    user_name.short_description = 'Doctor'

    def specializations_list(self, obj):
        return ", ".join([s.name for s in obj.specializations.all()[:3]])
    specializations_list.short_description = 'Specializations'

    def is_verified_badge(self, obj):
        if hasattr(obj, 'is_verified') and obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: orange;">Pending</span>')
    is_verified_badge.short_description = 'Status'

    def rating_display(self, obj):
        return f"⭐ {obj.rating} ({obj.total_reviews})"
    rating_display.short_description = 'Rating'


@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'patient_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('doctor__user__first_name', 'patient__first_name', 'comment')
    readonly_fields = ('created_at',)

    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"
    doctor_name.short_description = 'Doctor'

    def patient_name(self, obj):
        return obj.patient.get_full_name() or obj.patient.username
    patient_name.short_description = 'Patient'
