from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import timedelta
import uuid

class UserProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('general', 'General Mechanic'),
        ('engine', 'Engine Specialist'),
        ('electrical', 'Electrical Systems'),
        ('brakes', 'Brakes & Suspension'),
        ('diagnostics', 'Diagnostics'),
    ]

    phone_validator = RegexValidator(
        regex=r'^\+\d{1,3}\s?\d{10}$',
        message='Phone number must be in the format: +<country code> <10 digits>, e.g., +91 9876543210'
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, validators=[phone_validator], blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_user = models.BooleanField(default=True)
    is_mechanic = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True)
    experience = models.IntegerField(null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    certifications = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        from django.templatetags.static import static
        return static('img/default-avatar.png')

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username


class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash on Hand'),
        ('online', 'Online Payment'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests')
    mechanic = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    issue_description = models.TextField(blank=True, null=True)
    vehicle_type = models.CharField(max_length=100, blank=True, null=True)
    vehicle_make = models.CharField(max_length=50, blank=True, null=True)
    vehicle_model = models.CharField(max_length=50, blank=True, null=True)
    vehicle_year = models.IntegerField(blank=True, null=True)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_license = models.CharField(max_length=20, blank=True, null=True)
    preferred_datetime = models.DateTimeField(blank=True, null=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    otp = models.CharField(max_length=8, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    additional_notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')

    def __str__(self):
        return f"Service Request #{self.id} for {self.customer.username}"


class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('en_route', 'En Route'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='jobs')
    mechanic = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rating = models.FloatField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)  # Added null=True
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Job #{self.id} for {self.service_request.customer.username}"


class Invoice(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.invoice_number:
                self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            if not self.due_date:
                self.due_date = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    METHOD_CHOICES = [('card', 'Credit/Debit Card'), ('upi', 'UPI')]
    CARD_TYPE_CHOICES = [('visa', 'Visa'), ('mastercard', 'Mastercard'), ('amex', 'American Express'), ('discover', 'Discover')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=50, choices=METHOD_CHOICES, default='card')
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.CharField(max_length=5, blank=True, null=True)
    cvv = models.CharField(max_length=4, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method_type} ending in {self.card_number[-4:] if self.card_number else self.upi_id}"


class MechanicLocation(models.Model):
    mechanic = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='mechanic_locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Location for {self.mechanic.username} at {self.timestamp}"


# Signal to create or update user profile
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()
