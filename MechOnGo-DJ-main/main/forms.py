from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ServiceRequest, PaymentMethod
import re
from datetime import datetime, timedelta
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+\d{1,3}\s?\d{10}$',
    message='Phone number must be in the format: +<country code> <10 digits>, e.g., +91 9876543210'
)

class BaseSignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')
    phone = forms.CharField(
        max_length=15,
        required=True,
        help_text='Required. Enter your phone number in format: +91 9876543210',
        validators=[phone_validator]
    )
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    terms = forms.BooleanField(required=True, error_messages={'required': 'You must agree to the terms and conditions.'})

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'terms')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError('Username can only contain letters, numbers, and @/./+/-/_ characters.')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password1

class UserSignUpForm(BaseSignUpForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': self.cleaned_data['phone'],
                    'is_user': True,
                    'is_mechanic': False
                }
            )
        return user

class MechanicSignUpForm(BaseSignUpForm):
    specialization = forms.ChoiceField(
        choices=UserProfile.SPECIALIZATION_CHOICES,
        required=True
    )
    years_of_experience = forms.IntegerField(
        min_value=0,
        max_value=50,
        required=True
    )
    certifications = forms.CharField(
        widget=forms.Textarea,
        required=False
    )

    class Meta(BaseSignUpForm.Meta):
        fields = BaseSignUpForm.Meta.fields + ('specialization', 'years_of_experience', 'certifications')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': self.cleaned_data['phone'],
                    'is_user': False,
                    'is_mechanic': True,
                    'specialization': self.cleaned_data['specialization'],
                    'years_of_experience': self.cleaned_data['years_of_experience'],
                    'certifications': self.cleaned_data['certifications'],
                    'is_approved': False
                }
            )
        return user

class MechanicProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    
    phone = forms.CharField(
        max_length=15,
        required=True,
        validators=[phone_validator]
    )
    avatar = forms.ImageField(required=False)
    specialization = forms.ChoiceField(
        choices=UserProfile.SPECIALIZATION_CHOICES,
        required=True
    )
    years_of_experience = forms.IntegerField(
        min_value=0,
        max_value=50,
        required=True
    )
    certifications = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar', 'specialization', 'years_of_experience', 'certifications']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username != self.user.username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError('Username can only contain letters, numbers, and @/./+/-/_ characters.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.user.email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
                profile.save()
        return profile

class ServiceRequestForm(forms.ModelForm):
    issue_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'class': 'form-textarea',
            'placeholder': 'e.g., Car makes a strange noise when accelerating'
        }),
        required=True,
        help_text='Describe the issue with your vehicle.'
    )
    preferred_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-input flatpickr-input',
            'placeholder': 'Select date'
        }),
        initial=lambda: datetime.now().date()
    )
    preferred_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'text',
            'class': 'form-input flatpickr-input',
            'placeholder': 'Select time'
        }),
        initial=lambda: (datetime.now() + timedelta(hours=1)).time().replace(minute=0, second=0)
    )
    vehicle_make = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., Toyota'
        })
    )
    vehicle_model = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., Camry'
        })
    )
    vehicle_year = forms.IntegerField(
        min_value=1900,
        max_value=datetime.now().year + 1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 2020'
        })
    )
    vehicle_license = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., ABC123'
        })
    )
    location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 123 Main St, Springfield'
        }),
        required=True
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '(123) 456-7890'
        }),
        required=True
    )
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-textarea',
            'placeholder': 'Any additional information or special requests'
        }),
        required=False
    )
    payment_method = forms.ChoiceField(
        choices=ServiceRequest.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        initial='cash'
    )
    estimated_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g., 49.99'
        }),
        help_text='Estimated cost of the service (optional, will be confirmed by mechanic).'
    )

    class Meta:
        model = ServiceRequest
        fields = [
            'issue_description', 'preferred_date', 'preferred_time',
            'vehicle_make', 'vehicle_model', 'vehicle_year',
            'vehicle_license', 'location', 'phone_number',
            'additional_notes', 'payment_method', 'estimated_cost'
        ]

    def clean(self):
        cleaned_data = super().clean()
        preferred_date = cleaned_data.get('preferred_date')
        preferred_time = cleaned_data.get('preferred_time')
        payment_method = cleaned_data.get('payment_method')
        estimated_cost = cleaned_data.get('estimated_cost')
        phone_number = cleaned_data.get('phone_number')
        
        if preferred_date and preferred_time:
            preferred_datetime = datetime.combine(preferred_date, preferred_time)
            if preferred_datetime < datetime.now():
                raise forms.ValidationError("You cannot select a date/time in the past.")
        
        if estimated_cost and estimated_cost < 0:
            raise forms.ValidationError("Estimated cost cannot be negative.")
        
        if phone_number:
            cleaned_phone = re.sub(r'\D', '', phone_number)
            if not cleaned_phone.isdigit() or len(cleaned_phone) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            cleaned_data['phone_number'] = f"({cleaned_phone[:3]}) {cleaned_phone[3:6]}-{cleaned_phone[6:]}"
        
        if payment_method == 'online':
            card_number = self.data.get('card_number', '').replace(' ', '')
            expiry_date = self.data.get('expiry_date', '')
            cvv = self.data.get('cvv', '')
            card_name = self.data.get('card_name', '')
            
            if not card_number or not card_number.isdigit() or len(card_number) != 16:
                self.add_error(None, "Please enter a valid 16-digit card number.")
            if not expiry_date or not re.match(r'^(0[1-9]|1[0-2])/[0-9]{2}$', expiry_date):
                self.add_error(None, "Please enter a valid expiry date in MM/YY format.")
            if not cvv or not cvv.isdigit() or len(cvv) != 3:
                self.add_error(None, "Please enter a valid 3-digit CVV.")
            if not card_name or len(card_name.strip()) < 2:
                self.add_error(None, "Please enter a valid name on card.")
        
        return cleaned_data

class PaymentMethodForm(forms.ModelForm):
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '1234 5678 9012 3456'
        }),
        label='Card Number'
    )
    expiry_date = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'MM/YY'
        }),
        label='Expiry Date'
    )
    cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '123'
        }),
        label='CVV'
    )
    cardholder_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'John Smith'
        }),
        label='Name on Card'
    )

    class Meta:
        model = PaymentMethod
        fields = ['card_type', 'card_number', 'expiry_date', 'cvv', 'cardholder_name']

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number').replace(' ', '')
        if not card_number.isdigit() or len(card_number) != 16:
            raise forms.ValidationError("Please enter a valid 16-digit card number.")
        if card_number.startswith('4'):
            self.cleaned_data['card_type'] = 'visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            self.cleaned_data['card_type'] = 'mastercard'
        elif card_number.startswith('34') or card_number.startswith('37'):
            self.cleaned_data['card_type'] = 'amex'
        elif card_number.startswith('6011'):
            self.cleaned_data['card_type'] = 'discover'
        else:
            raise forms.ValidationError("Unsupported card type.")
        return card_number[-4:]

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date')
        if not re.match(r'^(0[1-9]|1[0-2])/[0-9]{2}$', expiry_date):
            raise forms.ValidationError("Please enter a valid expiry date in MM/YY format.")
        month, year = map(int, expiry_date.split('/'))
        current_year = datetime.now().year % 100
        if year < current_year or (year == current_year and month < datetime.now().month):
            raise forms.ValidationError("Card has expired.")
        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')
        if not cvv.isdigit() or len(cvv) not in (3, 4):
            raise forms.ValidationError("Please enter a valid CVV (3 or 4 digits).")
        return cvv

    def clean_cardholder_name(self):
        cardholder_name = self.cleaned_data.get('cardholder_name').strip()
        if len(cardholder_name) < 2:
            raise forms.ValidationError("Please enter a valid name on card.")
        return cardholder_name

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.last_four = self.cleaned_data['card_number']
        if commit:
            instance.save()
        return instance