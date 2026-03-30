from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Doctor, Specialization
from appointments_app.models import TimeSlot


class DoctorListView(View):
    """List all doctors with filtering and pagination."""
    template_name = 'doctors/listing.html'
    paginate_by = 9

    def get(self, request):
        # Get filter parameters
        specializations = request.GET.getlist('specialization')
        min_fee = request.GET.get('min_fee')
        max_fee = request.GET.get('max_fee')
        experience = request.GET.get('experience')
        availability = request.GET.get('availability')
        search = request.GET.get('q')

        # Base queryset
        doctors = Doctor.objects.select_related('user').prefetch_related('specializations').filter(
            is_accepting_patients=True
        )

        # Apply filters
        if specializations:
            doctors = doctors.filter(specializations__id__in=specializations).distinct()

        if min_fee:
            doctors = doctors.filter(consultation_fee__gte=min_fee)

        if max_fee:
            doctors = doctors.filter(consultation_fee__lte=max_fee)

        if experience:
            doctors = doctors.filter(years_of_experience__gte=experience)

        # Availability filter
        if availability:
            from django.utils import timezone
            today = timezone.now().date()
            if availability == 'today':
                from appointments_app.models import TimeSlot
                doctors = doctors.filter(time_slots__date=today, time_slots__is_available=True).distinct()
            elif availability == 'week':
                from appointments_app.models import TimeSlot
                end_date = today + timedelta(days=7)
                doctors = doctors.filter(
                    time_slots__date__gte=today,
                    time_slots__date__lt=end_date,
                    time_slots__is_available=True
                ).distinct()

        if search:
            doctors = doctors.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specializations__name__icontains=search)
            ).distinct()

        # Annotate available slots count for today
        from django.utils import timezone
        today = timezone.now().date()
        from django.db.models import Count
        doctors = doctors.annotate(
            available_slots_count=Count(
                'time_slots',
                filter=Q(time_slots__date=today, time_slots__is_available=True)
            )
        )

        # Get all specializations for filter dropdown
        all_specializations = Specialization.objects.all()

        # Pagination
        paginator = Paginator(doctors, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'specializations': all_specializations,
            'selected_specializations': specializations,
            'selected_min_fee': min_fee,
            'selected_max_fee': max_fee or 500,
            'selected_experience': experience,
            'selected_availability': availability,
            'search_query': search,
        }
        return render(request, self.template_name, context)


class DoctorDetailView(View):
    """Display doctor profile with available time slots."""
    template_name = 'doctors/profile.html'

    def get(self, request, pk):
        doctor = get_object_or_404(
            Doctor.objects.select_related('user').prefetch_related('specializations', 'reviews__patient'),
            pk=pk,
            is_accepting_patients=True
        )

        # Get available time slots for next 7 days
        today = datetime.now().date()
        end_date = today + timedelta(days=7)

        time_slots = TimeSlot.objects.filter(
            doctor=doctor,
            date__gte=today,
            date__lt=end_date,
            is_available=True
        ).order_by('date', 'start_time')

        # Group time slots by date
        slots_by_date = {}
        slots_json = {}
        for slot in time_slots:
            date_str = slot.date.strftime('%Y-%m-%d')
            if date_str not in slots_by_date:
                slots_by_date[date_str] = {
                    'date': slot.date,
                    'slots': []
                }
            slots_by_date[date_str]['slots'].append(slot)

            # Build JSON for JavaScript
            if date_str not in slots_json:
                slots_json[date_str] = []
            slots_json[date_str].append({
                'id': slot.id,
                'date': slot.date.strftime('%Y-%m-%d'),
                'start_time': slot.start_time.strftime('%I:%M %p'),
                'end_time': slot.end_time.strftime('%I:%M %p'),
            })

        # Get clinic name from doctor profile if exists
        clinic_name = getattr(doctor, 'clinic_name', None)

        context = {
            'doctor': doctor,
            'slots_by_date': slots_by_date,
            'slots_json': slots_json,
            'today': today,
            'clinic_name': clinic_name,
        }
        return render(request, self.template_name, context)


class DoctorSearchView(View):
    """AJAX-compatible search for doctors."""
    template_name = 'doctors/partials/list.html'

    def get(self, request):
        search = request.GET.get('q', '')
        specialization = request.GET.get('specialization')
        max_fee = request.GET.get('max_fee')
        page = request.GET.get('page', 1)

        doctors = Doctor.objects.select_related('user').prefetch_related('specializations').filter(
            is_accepting_patients=True
        )

        if search:
            doctors = doctors.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specializations__name__icontains=search)
            ).distinct()

        if specialization:
            doctors = doctors.filter(specializations__id=specialization)

        if max_fee:
            doctors = doctors.filter(consultation_fee__lte=max_fee)

        # Pagination
        paginator = Paginator(doctors, 9)
        page_obj = paginator.get_page(page)

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if is_ajax:
            return render(request, self.template_name, {'page_obj': page_obj})

        return render(request, 'doctors/search.html', {
            'page_obj': page_obj,
            'search': search,
            'specialization': specialization,
            'max_fee': max_fee,
        })