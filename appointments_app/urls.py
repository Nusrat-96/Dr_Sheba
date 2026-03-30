from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('book/<int:doctor_id>/', views.BookAppointmentView.as_view(), name='book'),
    path('cancel/<int:pk>/', views.CancelAppointmentView.as_view(), name='cancel'),
    path('confirm/<int:pk>/', views.ConfirmAppointmentView.as_view(), name='confirm'),
    path('detail/<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
]