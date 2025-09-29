from django.contrib import admin
from .models import (
    UserProfile, ServiceRequest, Job, PaymentMethod, Invoice
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_mechanic', 'is_user', 'is_admin', 'specialization', 'is_approved')
    list_filter = ('is_mechanic', 'is_user', 'is_admin', 'specialization', 'is_approved')
    search_fields = ('user__username', 'phone')
    readonly_fields = ('user',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'mechanic', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('customer__username', 'mechanic__username', 'vehicle_license')
    date_hierarchy = 'created_at'
    list_select_related = ('customer', 'mechanic')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_request', 'mechanic', 'start_time', 'end_time', 'status', 'rating')
    list_filter = ('status',)
    search_fields = ('service_request__customer__username', 'mechanic__username')
    date_hierarchy = 'start_time'
    list_select_related = ('service_request', 'mechanic')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_type', 'last_four', 'expiry_date', 'created_at')
    list_filter = ('card_type', 'created_at')
    search_fields = ('user__username', 'cardholder_name')
    list_select_related = ('user',)

    def last_four(self, obj):
        if obj.card_number:
            return obj.card_number[-4:]
        elif obj.upi_id:
            return obj.upi_id
        return 'N/A'
    last_four.short_description = 'Last Four Digits / UPI ID'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'job', 'amount', 'status', 'issued_at', 'due_date', 'paid_at')
    list_filter = ('status', 'issued_at', 'due_date', 'paid_at')
    search_fields = ('invoice_number', 'user__username', 'job__service_request__customer__username')
    date_hierarchy = 'issued_at'
    list_select_related = ('user', 'job')