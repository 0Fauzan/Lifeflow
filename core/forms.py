from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Donor, Hospital, Donation, BloodRequest, Camp, BloodInventory


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-control'}))


class DonorRegisterForm(UserCreationForm):
    first_name  = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name   = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email       = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone       = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}))
    city        = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    blood_group = forms.ChoiceField(choices=Donor.BLOOD_GROUPS, widget=forms.Select(attrs={'class': 'form-control'}))
    dob         = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gender      = forms.ChoiceField(choices=Donor.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    weight_kg   = forms.DecimalField(required=False, min_value=45, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '60'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'password1', 'password2']:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role       = 'donor'
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data.get('phone')
        user.city       = self.cleaned_data.get('city')
        if commit:
            user.save()
            Donor.objects.create(
                user=user,
                blood_group=self.cleaned_data['blood_group'],
                dob=self.cleaned_data['dob'],
                gender=self.cleaned_data.get('gender', ''),
                weight_kg=self.cleaned_data.get('weight_kg'),
            )
        return user


class HospitalRegisterForm(UserCreationForm):
    first_name    = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person Name'}))
    email         = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone         = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}))
    city          = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    hospital_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital Name'}))
    license_no    = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License Number'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'password1', 'password2']:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role       = 'hospital'
        user.first_name = self.cleaned_data['first_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data.get('phone')
        user.city       = self.cleaned_data.get('city')
        if commit:
            user.save()
            Hospital.objects.create(
                user=user,
                hospital_name=self.cleaned_data['hospital_name'],
                license_no=self.cleaned_data.get('license_no') or None,
            )
        return user


class DonationForm(forms.ModelForm):
    class Meta:
        model  = Donation
        fields = ['blood_group', 'units_donated', 'donation_date', 'camp', 'notes']
        widgets = {
            'blood_group':   forms.Select(attrs={'class': 'form-control'}),
            'units_donated': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5', 'max': '2'}),
            'donation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'camp':          forms.Select(attrs={'class': 'form-control'}),
            'notes':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Camp
        self.fields['camp'].queryset = Camp.objects.filter(status__in=['upcoming', 'ongoing'])
        self.fields['camp'].empty_label = '— None / Walk-in —'
        self.fields['camp'].required = False


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model  = BloodRequest
        fields = ['patient_name', 'blood_group', 'units_needed', 'urgency', 'reason']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of patient'}),
            'blood_group':  forms.Select(attrs={'class': 'form-control'}),
            'units_needed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5'}),
            'urgency':      forms.Select(attrs={'class': 'form-control'}),
            'reason':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Medical condition or reason...'}),
        }


class CampForm(forms.ModelForm):
    class Meta:
        model  = Camp
        fields = ['name', 'location', 'city', 'camp_date', 'start_time', 'end_time', 'organizer', 'capacity']
        widgets = {
            'name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Camp Name'}),
            'location':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue / Address'}),
            'city':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'camp_date':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time':   forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'organizer':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organizer Name'}),
            'capacity':   forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }


class InventoryUpdateForm(forms.Form):
    BLOOD_GROUPS = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    OP_CHOICES = [('add', 'Add to existing'), ('set', 'Set exact value')]

    blood_group = forms.ChoiceField(choices=BLOOD_GROUPS, widget=forms.Select(attrs={'class': 'form-control'}))
    units       = forms.IntegerField(min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Units'}))
    operation   = forms.ChoiceField(choices=OP_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone', 'city', 'address', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'city':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'address':    forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Full address...', 'rows': 3}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }