from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('appointments/', views.AllAppointmentsView.as_view(), name='appointments'),
    path('users/', views.AllUsersView.as_view(), name='users'),
    path('approve-doctor/<int:doctor_id>/', views.ApproveDoctorView.as_view(), name='approve_doctor'),
    path('reject-doctor/<int:doctor_id>/', views.RejectDoctorView.as_view(), name='reject_doctor'),
]
