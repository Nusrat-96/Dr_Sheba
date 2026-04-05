from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'address')
        }),
    )


# class UserAdminHandle(BaseUserAdmin):
#     user_list_display = ('username', 'email', 'role', 'is_staff')
#     user_list_filter = ('role', 'is_staff', 'is_active')
#     search_fields = ('username', 'first_name', 'is_active')
#     search_fields = ('username', 'first_name', 'last_name', 'email')
    

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'blood_group', 'date_of_birth', 'created')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created',)

    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'Patient'

    def created(self, obj):
        return obj.user.created_at.strftime('%Y-%m-%d')
    created.short_description = 'Registered'


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'specialty', 'license_number', 'is_verified', 'consultation_fee')
    list_filter = ('is_verified', 'specialty')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'license_number')
    list_editable = ('is_verified',)

    def user_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"
    user_name.short_description = 'Doctor'
