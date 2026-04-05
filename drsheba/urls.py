from django.contrib import admin
from django.urls import path, include
from accounts_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LandingPageView.as_view(), name='home'),  # Landing page at /
    path('accounts/', include('allauth.urls')),  # Allauth auth routes
    path('accounts/register/', views.RegisterChooseView.as_view(), name='register_choose'),
    path('accounts/signup/patient/', views.PatientSignupView.as_view(), name='patient_signup'),
    path('accounts/signup/doctor/', views.DoctorSignupView.as_view(), name='doctor_signup'),
    path('accounts/login/redirect/', views.RoleBasedRedirectView.as_view(), name='role_redirect'),
    path('doctors/', include('doctors_app.urls')),
    path('appointments/', include('appointments_app.urls')),
    path('dashboard/', include('dashboard_app.urls')),
    path('adminpanel/', include('adminpanel_app.urls')),
]
