from django.urls import path, include
from accounts_app import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='home'),
    path('accounts/', include('allauth.urls')),
    path('accounts/register/', views.RegisterChooseView.as_view(), name='register_choose'),
    path('accounts/signup/patient/', views.PatientSignupView.as_view(), name='patient_signup'),
    path('accounts/signup/doctor/', views.DoctorSignupView.as_view(), name='doctor_signup'),
    path('accounts/login/redirect/', views.RoleBasedRedirectView.as_view(), name='role_redirect'),
]