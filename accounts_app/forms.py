from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from accounts_app.models import PatientProfile, DoctorProfile
from doctors_app.models import Specialization

User = get_user_model()


class PatientSignupForm(UserCreationForm):
    """Registration form for patients."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    blood_group = forms.ChoiceField(
        choices=[('', 'Select Blood Group'), ('A+', 'A+'), ('A-', 'A-'),
                 ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'),
                 ('AB+', 'AB+'), ('AB-', 'AB-')],
        required=False
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'blood_group', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = 'patient'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            PatientProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                blood_group=self.cleaned_data.get('blood_group', '')
            )
        return user


class DoctorSignupForm(UserCreationForm):
    """Registration form for doctors."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        required=True,
        help_text='Select your primary specialization'
    )
    clinic_name = forms.CharField(max_length=200, required=True)
    experience_years = forms.IntegerField(min_value=0, required=True)
    consultation_fee = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=True)
    bio = forms.CharField(widget=forms.Textarea, required=False, max_length=500)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'specialization',
                  'clinic_name', 'experience_years', 'consultation_fee', 'bio',
                  'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = 'doctor'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            from doctors_app.models import Doctor
            doctor = Doctor.objects.create(
                user=user,
                consultation_fee=self.cleaned_data['consultation_fee'],
                years_of_experience=self.cleaned_data['experience_years'],
                bio=self.cleaned_data.get('bio', '')
            )
            doctor.specializations.add(self.cleaned_data['specialization'])

            DoctorProfile.objects.create(
                user=user,
                specialty=self.cleaned_data['specialization'].name,
                license_number=f"LIC-{user.id}",
                consultation_fee=self.cleaned_data['consultation_fee'],
                years_of_experience=self.cleaned_data['experience_years'],
                bio=self.cleaned_data.get('bio', '')
            )
        return user