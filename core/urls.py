from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',        views.index,        name='login'),
    path('logout/', views.logout_view,  name='logout'),

    # Admin
    path('admin-panel/',             views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/donations/',   views.admin_donations, name='admin_donations'),
    path('admin-panel/requests/',    views.admin_requests,  name='admin_requests'),
    path('admin-panel/inventory/',   views.admin_inventory, name='admin_inventory'),
    path('admin-panel/donors/',      views.admin_donors,    name='admin_donors'),
    path('admin-panel/camps/',       views.admin_camps,     name='admin_camps'),
    path('admin-panel/hospitals/',   views.admin_hospitals, name='admin_hospitals'),
    path('admin-panel/reports/',     views.admin_reports,   name='admin_reports'),

    # Donor
    path('donor/',          views.donor_dashboard, name='donor_dashboard'),
    path('donor/donate/',   views.donor_donate,    name='donor_donate'),
    path('donor/history/',  views.donor_history,   name='donor_history'),
    path('donor/camps/',    views.donor_camps,     name='donor_camps'),
    path('donor/profile/',  views.donor_profile,   name='donor_profile'),

    # Hospital
    path('hospital/',              views.hospital_dashboard,   name='hospital_dashboard'),
    path('hospital/request/',      views.hospital_request,     name='hospital_request'),
    path('hospital/my-requests/',  views.hospital_my_requests, name='hospital_my_requests'),
    path('hospital/inventory/',    views.hospital_inventory,   name='hospital_inventory'),
]
