from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts_app.urls')),
    path('doctors/', include('doctors_app.urls')),
]