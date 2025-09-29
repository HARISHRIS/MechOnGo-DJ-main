import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import random
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import MechanicProfileForm, UserSignUpForm, MechanicSignUpForm, ServiceRequestForm, PaymentMethodForm
from .models import UserProfile, ServiceRequest, Job, Invoice, PaymentMethod

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"User {user.username} signed up and logged in successfully")
            return redirect('customer_dashboard')
        else:
            logger.error(f"Signup form errors: {form.errors}, Submitted data: {request.POST}")
    else:
        form = UserSignUpForm()
    return render(request, 'Authentication/signup.html', {'form': form, 'is_mechanic_signup': False})

def mechanic_signup(request):
    if request.method == 'POST':
        form = MechanicSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"Mechanic {user.username} signed up and logged in successfully")
            return redirect('mechanic_dashboard')
        else:
            logger.error(f"Mechanic signup form errors: {form.errors}, Submitted data: {request.POST}")
    else:
        form = MechanicSignUpForm()
    return render(request, 'Authentication/signup.html', {'form': form, 'is_mechanic_signup': True})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info(f"User {user.username} logged in successfully")
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': "",
                    'is_user': True,
                    'is_mechanic': False
                }
            )
            if profile.is_mechanic:
                logger.info(f"Redirecting {user.username} to mechanic_dashboard")
                return redirect('mechanic_dashboard')
            else:
                logger.info(f"Redirecting {user.username} to customer_dashboard")
                return redirect('customer_dashboard')
        else:
            logger.error(f"Login form errors: {form.errors}, Submitted data: {request.POST}")
    else:
        form = AuthenticationForm()
    return render(request, 'Authentication/login.html', {'form': form})

def logout_view(request):
    logout(request)
    logger.info("User logged out")
    return redirect('home')

def home(request):
    if request.user.is_authenticated:
        logger.info(f"Authenticated user {request.user.username} accessed home page")
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'phone': "",
                'is_user': True,
                'is_mechanic': False
            }
        )
        if profile.is_mechanic:
            logger.info(f"Redirecting {request.user.username} to mechanic_dashboard")
            return redirect('mechanic_dashboard')
        else:
            logger.info(f"Redirecting {request.user.username} to customer_dashboard")
            return redirect('customer_dashboard')
    return render(request, 'general/home.html')

def about(request):
    return render(request, 'general/about.html')

def service(request):
    return render(request, 'general/services.html')

def team(request):
    return render(request, 'general/team.html')

@login_required
def mechanic_dashboard(request):
    if not request.user.profile.is_mechanic:
        return redirect('home')

    # Query 1: New requests for ANY mechanic to accept.
    new_requests_query = ServiceRequest.objects.filter(
        mechanic=None, status='pending'
    ).select_related('customer').order_by('-created_at')

    # Query 2: Jobs ASSIGNED TO THIS MECHANIC that are active (scheduled or in progress).
    # This is the list that will correctly show "Start" or "Complete".
    my_active_jobs = Job.objects.filter(
        mechanic=request.user,
        status__in=['scheduled', 'in_progress']
    ).select_related(
        'service_request', 
        'service_request__customer'
    ).order_by('start_time')

    # Stats cards data
    completed_jobs_count = Job.objects.filter(
        mechanic=request.user, status='completed'
    ).count()
    ratings = Job.objects.filter(
        mechanic=request.user, status='completed', rating__isnull=False
    ).values_list('rating', flat=True)
    average_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
    
    # We will get "Today's Appointments" count from the my_active_jobs query
    today = timezone.now().date()
    todays_appointments_count = sum(1 for job in my_active_jobs if job.start_time.date() == today)


    context = {
        'new_requests_count': new_requests_query.count(),
        'completed_jobs': completed_jobs_count,
        'average_rating': average_rating,
        'todays_appointments_count': todays_appointments_count,
        'new_service_requests': new_requests_query,  # For the "Accept" list
        'my_active_jobs': my_active_jobs,            # For the "Start/Complete" list
    }
    return render(request, 'Mechanic/mechanic_dashboard.html', context)


@login_required
def accept_service_request(request, request_id):
    if not request.user.profile.is_mechanic:
        return redirect('home')
    if request.method == 'POST':
        try:
            service_request = ServiceRequest.objects.get(id=request_id, mechanic=None, status='pending')
            job = Job.objects.filter(service_request=service_request).first()

            if not job:
                # This case shouldn't happen with the current book_service logic, but it's a good safeguard
                messages.error(request, "Cannot accept request: Corresponding job not found.")
                return redirect('mechanic_dashboard')

            service_request.mechanic = request.user
            service_request.status = 'accepted'
            
            job.mechanic = request.user
            job.status = 'scheduled'

            service_request.save()
            job.save()

            messages.success(request, f"Service request for {service_request.customer.get_full_name()} has been accepted.")
            return redirect('mechanic_dashboard')
        except ServiceRequest.DoesNotExist:
            messages.error(request, "Service request not found or already assigned.")
            return redirect('mechanic_dashboard')
    return redirect('mechanic_dashboard')


@login_required
def start_job_otp(request, service_request_id):
    """Renders the OTP page for starting a job."""
    service_request = get_object_or_404(ServiceRequest, id=service_request_id, mechanic=request.user)
    context = {
        'service_request': service_request,
        'action': 'start',
        'mobile_number': service_request.phone_number,  # Add this for consistency
    }
    return render(request, 'Mechanic/otp_verification.html', context)

@login_required
def complete_job_otp(request, service_request_id):
    """Renders the OTP page for completing a job."""
    service_request = get_object_or_404(ServiceRequest, id=service_request_id, mechanic=request.user)
    context = {
        'service_request': service_request,
        'action': 'complete',
        'mobile_number': service_request.phone_number, # Add this for consistency
    }
    return render(request, 'Mechanic/otp_verification.html', context)

@login_required
def verify_otp(request, service_request_id):
    """Handles both sending and verifying the OTP via POST request."""
    if not request.user.profile.is_mechanic:
        return redirect('home')

    service_request = get_object_or_404(ServiceRequest, id=service_request_id, mechanic=request.user)
    job = get_object_or_404(Job, service_request=service_request)
    action = request.POST.get('action') # 'start' or 'complete'

    if request.method != 'POST':
        return HttpResponseRedirect(reverse('mechanic_dashboard'))
    
    context_for_render = {
        'service_request': service_request,
        'action': action,
        'mobile_number': service_request.phone_number
    }

    # --- Send OTP Logic ---
    if 'send_otp' in request.POST:
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        action_char = 'S' if action == 'start' else 'C'
        
        service_request.otp = f"{otp}-{action_char}"
        service_request.otp_created_at = timezone.now()
        service_request.save()
        
        logger.info(f"Generated OTP {otp} for service request {service_request_id} (action: {action})")
        messages.success(request, f"OTP has been generated and is now visible to the customer.")
        context_for_render['otp_sent'] = True # To show a success message in template

    # --- Verify OTP Logic ---
    elif 'verify_otp' in request.POST:
        entered_otp = request.POST.get('otp')
        
        if not service_request.otp or not service_request.otp_created_at:
            messages.error(request, "No valid OTP found. Please generate a new one.")
        elif (timezone.now() - service_request.otp_created_at).total_seconds() > 300: # 5 minutes expiry
            messages.error(request, "OTP has expired. Please generate a new one.")
        elif entered_otp == service_request.otp.split('-')[0]:
            otp_action_char = service_request.otp.split('-')[1]
            
            # Check if the OTP action matches the form action
            if (action == 'start' and otp_action_char == 'S') or (action == 'complete' and otp_action_char == 'C'):
                if action == 'start':
                    job.status = 'in_progress'
                    messages.success(request, "Job started successfully.")
                else: # complete
                    job.status = 'completed'
                    job.completed_at = timezone.now()
                    messages.success(request, "Job completed successfully.")
                
                job.save()
                
                # Clear OTP after use
                service_request.otp = None
                service_request.otp_created_at = None
                service_request.save()
                
                return redirect('mechanic_dashboard')
            else:
                messages.error(request, "This OTP is for a different action. Please use the correct OTP.")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'Mechanic/otp_verification.html', context_for_render)

@login_required
def service_requests(request):
    if not request.user.profile.is_mechanic:
        return redirect('home')
    return render(request, 'Mechanic/service_requests.html')

@login_required
def service_calendar(request):
    if not request.user.profile.is_mechanic:
        return redirect('home')
    return render(request, 'Mechanic/service_calendar.html')

@login_required
def job_history(request):
    if not request.user.profile.is_mechanic:
        return redirect('home')
    return render(request, 'Mechanic/job_history.html')

@login_required
def mechanic_profile(request):
    if not request.user.profile.is_mechanic:
        logger.warning(f"Unauthorized access to mechanic_profile by {request.user.username}")
        return redirect('home')
    
    profile = request.user.profile
    
    if request.method == 'POST':
        form = MechanicProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            logger.info(f"Profile updated for mechanic {request.user.username}")
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('mechanic_profile')
        else:
            logger.error(f"Profile update failed for {request.user.username}: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = MechanicProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'Mechanic/mechanic_profile.html', context)

@login_required
def customer_dashboard(request):
    if request.user.profile.is_mechanic:
        return redirect('home')

    active_bookings_count = Job.objects.filter(
        service_request__customer=request.user,
        status__in=['pending', 'scheduled', 'in_progress']
    ).count()
    
    completed_services_count = Job.objects.filter(
        service_request__customer=request.user, status='completed'
    ).count()
    
    ratings = Job.objects.filter(
        service_request__customer=request.user, status='completed', rating__isnull=False
    ).values_list('rating', flat=True)
    
    average_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
    
    next_appointment_job = Job.objects.filter(
        service_request__customer=request.user,
        status__in=['pending', 'scheduled'],
        start_time__gte=timezone.now()
    ).order_by('start_time').first()
    
    current_bookings = Job.objects.filter(
        service_request__customer=request.user,
        status__in=['pending', 'scheduled', 'in_progress']
    ).select_related('service_request', 'mechanic', 'mechanic__profile').order_by('start_time')
    
    # REFACTOR: Get OTPs from the model, not the session.
    otp_mapping = {}
    for job in current_bookings:
        sr = job.service_request
        if sr.otp and sr.otp_created_at and (timezone.now() - sr.otp_created_at).total_seconds() < 300:
            otp_code, action_char = sr.otp.split('-')
            action_text = 'start' if action_char == 'S' else 'complete'
            otp_mapping[sr.id] = {
                'otp': otp_code,
                'action': action_text
            }

    context = {
        'active_bookings': active_bookings_count,
        'completed_services': completed_services_count,
        'average_rating': average_rating,
        'next_appointment': next_appointment_job.start_time if next_appointment_job else None,
        'current_bookings': current_bookings,
        'otp_mapping': otp_mapping,
    }
    
    # Handle AJAX requests for polling
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'Customer/customer_dashboard.html', context)
        
    return render(request, 'Customer/customer_dashboard.html', context)

@login_required
def track_service(request):
    logger.info(f"Accessing track_service for user {request.user.username}")
    
    is_mechanic = request.user.profile.is_mechanic
    
    active_jobs_query = Job.objects.none() # Start with an empty queryset

    if is_mechanic:
        active_jobs_query = Job.objects.filter(
            mechanic=request.user,
            status__in=['scheduled', 'in_progress', 'en_route']
        )
    else:  # Customer
        active_jobs_query = Job.objects.filter(
            service_request__customer=request.user,
            status__in=['scheduled', 'in_progress', 'en_route']
        )
    
    active_jobs = active_jobs_query.select_related(
        'service_request', 
        'mechanic', 
        'mechanic__profile'
    ).order_by('start_time')
    
    # --- SOLUTION: Attach OTP data directly to each job object ---
    for job in active_jobs:
        job.otp_data = None  # Default to None
        sr = job.service_request
        if sr.otp and sr.otp_created_at and (timezone.now() - sr.otp_created_at).total_seconds() < 300:
            try:
                otp_code, action_char = sr.otp.split('-')
                action_text = 'start' if action_char == 'S' else 'complete'
                job.otp_data = {
                    'otp': otp_code,
                    'action': action_text
                }
            except ValueError:
                # Handle case where OTP format is incorrect
                logger.warning(f"Malformed OTP '{sr.otp}' found for ServiceRequest {sr.id}")

        # You can also attach the mechanic's address here if you have a location model
        # For now, we'll assume the template handles this part.
        
    context = {
        'active_jobs': active_jobs,
        'is_mechanic': is_mechanic,
    }
    return render(request, 'Customer/track_service.html', context)

@login_required
def order_history(request):
    return render(request, 'Customer/order_history.html')

@login_required
def rate_service(request):
    return render(request, 'Customer/rate_service.html')

@login_required
def book_service(request):
    if request.user.profile.is_mechanic:
        return redirect('home')
    
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            # FIX: Make datetime object timezone-aware before saving
            preferred_date = form.cleaned_data['preferred_date']
            preferred_time = form.cleaned_data['preferred_time']
            naive_datetime = datetime.combine(preferred_date, preferred_time)
            preferred_datetime = timezone.make_aware(naive_datetime, timezone.get_default_timezone())

            service_request = form.save(commit=False)
            service_request.customer = request.user
            service_request.preferred_datetime = preferred_datetime
            service_request.save()
            
            Job.objects.create(
                service_request=service_request,
                start_time=preferred_datetime,
                end_time=preferred_datetime + timedelta(hours=2), # Default duration
                status='pending'
            )
            
            # Creating an invoice here might be premature, but we'll follow the original logic
            Invoice.objects.create(
                user=request.user,
                job=service_request.jobs.first(),
                amount=service_request.estimated_cost or 0.00,
                status='pending'
            )

            messages.success(request, "Your service has been booked successfully!")
            return redirect('booking_confirmation', booking_id=service_request.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ServiceRequestForm()
    
    context = {'form': form}
    return render(request, 'Customer/book_service.html', context)

@login_required
def booking_confirmation(request, booking_id):
    if not request.user.is_authenticated or request.user.profile.is_mechanic:
        logger.warning(f"Unauthorized access to booking_confirmation by {request.user.username if request.user.is_authenticated else 'anonymous'}")
        return redirect('home')
    
    try:
        booking = ServiceRequest.objects.get(id=booking_id, customer=request.user)
        job = booking.jobs.first()
        return render(request, 'Customer/booking_confirmation.html', {
            'booking': booking,
            'job': job
        })
    except ServiceRequest.DoesNotExist:
        logger.warning(f"Booking {booking_id} not found for user {request.user.username}")
        return redirect('home')

@login_required
def payment_billing(request):
    if request.user.profile.is_mechanic:
        logger.warning(f"Mechanic user {request.user.username} attempted to access payment_billing")
        return redirect('home')
    
    pending_services = ServiceRequest.objects.filter(
        customer=request.user,
        jobs__status__in=['pending', 'scheduled', 'in_progress']
    ).prefetch_related('jobs').distinct().order_by('-created_at')
    
    invoices = Invoice.objects.filter(user=request.user).order_by('-issued_at')
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    payment_form = PaymentMethodForm(request.POST or None)
    
    if request.method == 'POST':
        if 'add_payment' in request.POST and payment_form.is_valid():
            payment_method = payment_form.save(commit=False)
            payment_method.user = request.user
            payment_method.save()
            logger.info(f"User {request.user.username} added payment method: {payment_method}")
            return redirect('payment_billing')
        elif 'pay_invoice' in request.POST:
            invoice_id = request.POST.get('invoice_id')
            payment_method_id = request.POST.get('payment_method_id')
            try:
                invoice = Invoice.objects.get(id=invoice_id, user=request.user, status='pending')
                payment_method = PaymentMethod.objects.get(id=payment_method_id, user=request.user)
                invoice.status = 'paid'
                invoice.paid_at = timezone.now()
                invoice.save()
                logger.info(f"User {request.user.username} paid invoice #{invoice.invoice_number}")
                return redirect('payment_billing')
            except (Invoice.DoesNotExist, PaymentMethod.DoesNotExist):
                logger.error(f"Payment failed for user {request.user.username}: Invalid invoice or payment method")
                payment_form.add_error(None, "Invalid invoice or payment method.")
    
    context = {
        'pending_services': pending_services,
        'invoices': invoices,
        'payment_methods': payment_methods,
        'payment_form': payment_form,
    }
    return render(request, 'Customer/payment_billing.html', context)

@login_required
def customer_profile(request):
    if request.user.profile.is_mechanic or not request.user.profile.is_user:
        logger.warning(f"Unauthorized access to customer_profile by {request.user.username}")
        return redirect('home')

    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile
            old_username = user.username
            old_email = user.email

            user.username = request.POST.get('username')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            
            if user.username != old_username and User.objects.filter(username=user.username).exists():
                messages.error(request, "This username is already taken.")
                logger.warning(f"Username {user.username} already taken for user {request.user.username}")
                return render(request, 'Customer/customer_profile.html')
            if user.email != old_email and User.objects.filter(email=user.email).exists():
                messages.error(request, "This email address is already in use.")
                logger.warning(f"Email {user.email} already in use for user {request.user.username}")
                return render(request, 'Customer/customer_profile.html')

            profile.phone = request.POST.get('phone')
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            user.save()
            profile.save()
            logger.info(f"User {user.username} updated their profile successfully")
            messages.success(request, "Profile updated successfully.")
            return redirect('customer_profile')
        except Exception as e:
            logger.error(f"Error updating profile for {request.user.username}: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while updating your profile. Please try again.")
    
    return render(request, 'Customer/customer_profile.html')


@login_required
def order_history(request):
    logger.info(f"Accessing order_history for user {request.user.username}")
    if request.user.profile.is_mechanic or not request.user.profile.is_user:
        logger.warning(f"Unauthorized access to order_history by {request.user.username}")
        return redirect('home')
    
    completed_jobs = Job.objects.filter(
        service_request__customer=request.user,
        status='completed'
    ).select_related('service_request', 'mechanic', 'mechanic__profile').order_by('-completed_at')
    
    context = {
        'completed_jobs': completed_jobs,
    }
    return render(request, 'Customer/order_history.html', context)

@login_required
def rate_service(request):
    """
    Allows a customer to rate and comment on their completed, unrated jobs.
    """
    if request.user.profile.is_mechanic:
        return redirect('home')

    # Handle the form submission
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        rating = request.POST.get('rating')
        comments = request.POST.get('comments', '').strip()
        
        # Basic validation
        if not job_id or not rating:
            messages.error(request, "A rating is required. Please select 1-5 stars.")
            return redirect('rate_service')

        try:
            job_to_rate = Job.objects.get(
                id=job_id,
                service_request__customer=request.user,
                status='completed',
                rating__isnull=True  # Ensure it hasn't been rated before
            )
            job_to_rate.rating = float(rating)
            job_to_rate.comments = comments
            job_to_rate.save()
            
            logger.info(f"User {request.user.username} submitted rating {rating} for job {job_id}")
            messages.success(request, f"Thank you for your feedback on the '{job_to_rate.service_request.issue_description[:30]}...' service!")
            return redirect('rate_service')
        
        except Job.DoesNotExist:
            logger.warning(f"User {request.user.username} tried to rate an invalid or already-rated job {job_id}")
            messages.error(request, "This job could not be found or has already been rated.")
            return redirect('rate_service')
        
        except (ValueError, TypeError):
            logger.error(f"Invalid rating value '{rating}' submitted by {request.user.username}")
            messages.error(request, "Invalid rating value provided. Please try again.")
            return redirect('rate_service')

    # Handle GET request (display the page)
    # Fetch all completed jobs for the user
    completed_jobs = Job.objects.filter(
        service_request__customer=request.user,
        status='completed'
    ).select_related(
        'service_request', 'mechanic', 'mechanic__profile'
    ).order_by('-completed_at')

    # Check for a specific job_id from the URL (e.g., from Order History)
    job_to_preselect = request.GET.get('job_id')

    context = {
        'completed_jobs': completed_jobs,
        'job_to_preselect': job_to_preselect,
    }
    return render(request, 'Customer/rate_service.html', context)

@login_required
def stop_location_sharing(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            job_id = data.get('job_id')
            job = Job.objects.get(id=job_id, mechanic=request.user, status='en_route')
            job.status = 'in_progress'
            job.save()
            return JsonResponse({'success': True})
        except Job.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Job not found or not authorized'})
        except Exception as e:
            logger.error(f"Error stopping location sharing: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Server error'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def service_calendar(request):
    if not request.user.profile.is_mechanic:
        logger.warning(f"Unauthorized access to service_calendar by {request.user.username}")
        return redirect('home')

    my_active_jobs = Job.objects.filter(
        mechanic=request.user,
        status__in=['scheduled', 'in_progress']
    ).select_related(
        'service_request', 
        'service_request__customer'
    ).order_by('start_time')

    logger.info(f"Rendering service calendar for {request.user.username} with {my_active_jobs.count()} active jobs")
    return render(request, 'Mechanic/service_calendar.html', {
        'my_active_jobs': my_active_jobs
    })

def custom_404(request, exception):
    logger.error(f"404 error for URL: {request.path}, User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    return render(request, 'general/404.html', status=404)