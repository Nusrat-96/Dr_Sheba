from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('patient/', views.PatientDashboardView.as_view(), name='patient'),
    path('doctor/', views.DoctorDashboardView.as_view(), name='doctor'),
    path('doctor/schedule/', views.DoctorScheduleView.as_view(), name='schedule'),
]
