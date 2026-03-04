from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Donor, Hospital, BloodInventory, Camp, CampRegistration, Donation, BloodRequest, Notification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'email', 'role', 'is_active']
    list_filter   = ['role', 'is_active']
    fieldsets     = UserAdmin.fieldsets + (('Role', {'fields': ('role', 'phone', 'city', 'address')}),)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display  = ['user', 'blood_group', 'total_donations', 'is_eligible', 'last_donation']
    list_filter   = ['blood_group', 'is_eligible']


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display  = ['hospital_name', 'user', 'verified']
    list_filter   = ['verified']


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display  = ['blood_group', 'units_available', 'last_updated']


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display  = ['name', 'city', 'camp_date', 'status', 'registered_count', 'capacity']
    list_filter   = ['status']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display  = ['donor', 'blood_group', 'units_donated', 'donation_date', 'status']
    list_filter   = ['status', 'blood_group']


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display  = ['patient_name', 'blood_group', 'units_needed', 'urgency', 'status', 'requester']
    list_filter   = ['status', 'urgency', 'blood_group']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'title', 'is_read', 'created_at']
    list_filter   = ['is_read']
