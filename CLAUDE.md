# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

drSheba is a Django 4.2.11 web application for doctor appointment booking with role-based authentication (patient, doctor, admin).

## Development Commands

```bash
# Activate virtual environment
env\Scripts\activate  # Windows

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run a specific app's tests
python manage.py test accounts_app

# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Architecture

### Custom User Model
The `accounts_app.User` model extends `AbstractUser` with:
- `role`: patient | doctor | admin
- `phone`, `address`, timestamps
- Related profiles: `PatientProfile`, `DoctorProfile`

### Apps
- **accounts_app** - Authentication, landing page, role-based signup (patient/doctor)
- **doctors_app** - Doctor profiles, specializations, reviews
- **appointments_app** - TimeSlot and Appointment booking models
- **dashboard_app** - Role-specific dashboards
- **adminpanel_app** - Admin interface

### URL Structure
- `/` → Landing page (accounts_app)
- `/accounts/` → Allauth auth routes
- `/accounts/login/redirect/` → Custom role-based redirect view
- `/doctors/` → Doctor list/detail/search
- `/appointments/` → Book/cancel/confirm appointments

### Authentication
- Uses django-allauth with email-based login
- `AUTH_USER_MODEL = 'accounts_app.User'`
- Custom redirect at login: `role_redirect` view determines dashboard based on user.role

### Database
- SQLite (`db.sqlite3`)
- Migrations exist for accounts_app, doctors_app, appointments_app
