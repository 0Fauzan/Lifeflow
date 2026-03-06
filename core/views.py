from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
from functools import wraps

from .models import (
    User, Donor, Hospital, BloodInventory, Camp,
    CampRegistration, Donation, BloodRequest, Notification
)
from .forms import (
    LoginForm, DonorRegisterForm, HospitalRegisterForm,
    DonationForm, BloodRequestForm, CampForm,
    InventoryUpdateForm, ProfileUpdateForm
)

# ─── DECORATORS ───────────────────────────────────────────────
def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, 'Access denied.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_inventory_map():
    return {inv.blood_group: inv for inv in BloodInventory.objects.all()}


# ─── AUTH VIEWS ───────────────────────────────────────────────
def index(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    login_form    = LoginForm()
    donor_form    = DonorRegisterForm()
    hospital_form = HospitalRegisterForm()
    active_tab    = 'login'
    active_reg    = 'donor'

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            active_tab = 'login'
            user = authenticate(
                request,
                username=request.POST.get('username'),
                password=request.POST.get('password')
            )
            if user:
                login(request, user)
                return redirect_by_role(user)
            else:
                messages.error(request, '❌ Invalid username or password.')

        elif action == 'register_donor':
            active_tab = 'register'
            active_reg = 'donor'
            donor_form = DonorRegisterForm(request.POST)
            if donor_form.is_valid():
                donor_form.save()
                messages.success(request, '✅ Donor account created! Please login.')
                return redirect('login')
            else:
                for field, errors in donor_form.errors.items():
                    for error in errors:
                        messages.error(request, f'❌ {field}: {error}')

        elif action == 'register_hospital':
            active_tab = 'register'
            active_reg = 'hospital'
            hospital_form = HospitalRegisterForm(request.POST)
            if hospital_form.is_valid():
                hospital_form.save()
                messages.success(request, '✅ Hospital account created! Pending admin verification.')
                return redirect('login')
            else:
                for field, errors in hospital_form.errors.items():
                    for error in errors:
                        messages.error(request, f'❌ {field}: {error}')

    return render(request, 'core/index.html', {
        'login_form':    login_form,
        'donor_form':    donor_form,
        'hospital_form': hospital_form,
        'active_tab':    active_tab,
        'active_reg':    active_reg,
    })


def logout_view(request):
    logout(request)
    return redirect('login')


def redirect_by_role(user):
    if user.role == 'admin':    return redirect('admin_dashboard')
    if user.role == 'donor':    return redirect('donor_dashboard')
    if user.role == 'hospital': return redirect('hospital_dashboard')
    return redirect('login')


# ══════════════════════════════════════════════════════════════
#  ADMIN VIEWS
# ══════════════════════════════════════════════════════════════

@role_required('admin')
def admin_dashboard(request):
    inventory     = BloodInventory.objects.all()
    total_units   = sum(i.units_available for i in inventory)
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:3]
    for n in notifications:
        n.is_read = True
        n.save()

    context = {
        'total_donors':      Donor.objects.count(),
        'total_hospitals':   Hospital.objects.count(),
        'total_units':       total_units,
        'pending_requests':  BloodRequest.objects.filter(status='pending').count(),
        'pending_donations': Donation.objects.filter(status='pending').count(),
        'total_donations':   Donation.objects.filter(status='approved').count(),
        'inventory':         inventory,
        'recent_requests':   BloodRequest.objects.select_related('requester').order_by('-request_date')[:8],
        'pending_don_list':  Donation.objects.filter(status='pending').select_related('donor__user')[:6],
        'notifications':     notifications,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@role_required('admin')
def admin_donations(request):
    if 'approve' in request.GET:
        donation = get_object_or_404(Donation, pk=request.GET['approve'])
        if donation.status == 'pending':
            with transaction.atomic():
                donation.status      = 'approved'
                donation.approved_by = request.user
                donation.save()
                inv, _ = BloodInventory.objects.get_or_create(
                    blood_group=donation.blood_group,
                    defaults={'units_available': 0}
                )
                inv.units_available += float(donation.units_donated)
                inv.save()
                donor = donation.donor
                donor.total_donations += 1
                donor.last_donation    = donation.donation_date
                donor.is_eligible      = False
                donor.save()
                if inv.units_available < 5:
                    for admin in User.objects.filter(role='admin'):
                        Notification.objects.create(
                            user=admin,
                            title=f'⚠️ Low Stock: {inv.blood_group}',
                            message=f'Blood group {inv.blood_group} is critically low ({inv.units_available} units).'
                        )
            messages.success(request, '✅ Donation approved and inventory updated!')
        return redirect('admin_donations')

    if 'reject' in request.GET:
        donation = get_object_or_404(Donation, pk=request.GET['reject'])
        donation.status      = 'rejected'
        donation.approved_by = request.user
        donation.save()
        messages.error(request, '❌ Donation rejected.')
        return redirect('admin_donations')

    status_filter = request.GET.get('s', '')
    qs = Donation.objects.select_related('donor__user', 'camp')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'admin_panel/donations.html', {'donations': qs, 'filter': status_filter})


@role_required('admin')
def admin_requests(request):
    if 'fulfill' in request.GET:
        req = get_object_or_404(BloodRequest, pk=request.GET['fulfill'])
        if req.status == 'pending':
            inv = BloodInventory.objects.filter(blood_group=req.blood_group).first()
            if inv and inv.units_available >= float(req.units_needed):
                with transaction.atomic():
                    inv.units_available -= float(req.units_needed)
                    inv.save()
                    req.status         = 'fulfilled'
                    req.fulfilled_date = date.today()
                    req.handled_by     = request.user
                    req.save()
                messages.success(request, '✅ Request fulfilled! Inventory deducted.')
            else:
                available = inv.units_available if inv else 0
                messages.error(request, f'❌ Insufficient stock. Available: {available} units.')
        return redirect('admin_requests')

    if 'reject' in request.GET:
        req = get_object_or_404(BloodRequest, pk=request.GET['reject'])
        req.status     = 'rejected'
        req.handled_by = request.user
        req.save()
        messages.error(request, '❌ Request rejected.')
        return redirect('admin_requests')

    urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    status_filter = request.GET.get('s', '')
    qs = BloodRequest.objects.select_related('requester')
    if status_filter:
        qs = qs.filter(status=status_filter)
    qs = sorted(qs, key=lambda r: urgency_order.get(r.urgency, 9))
    return render(request, 'admin_panel/requests.html', {'requests': qs, 'filter': status_filter})


@role_required('admin')
def admin_inventory(request):
    if request.method == 'POST':
        form = InventoryUpdateForm(request.POST)
        if form.is_valid():
            bg    = form.cleaned_data['blood_group']
            units = form.cleaned_data['units_to_add']
            inv, _ = BloodInventory.objects.get_or_create(blood_group=bg, defaults={'units_available': 0})
            inv.units_available += units
            inv.save()
            messages.success(request, f'✅ Added {units} units of {bg}.')
            return redirect('admin_inventory')
    else:
        form = InventoryUpdateForm()
    inventory = BloodInventory.objects.all()
    return render(request, 'admin_panel/inventory.html', {'inventory': inventory, 'form': form})


@role_required('admin')
def admin_donors(request):
    qs = Donor.objects.select_related('user')
    q  = request.GET.get('q', '')
    bg = request.GET.get('bg', '')
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(user__city__icontains=q)
        )
    if bg:
        qs = qs.filter(blood_group=bg)
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    return render(request, 'admin_panel/donors.html', {
        'donors': qs, 'query': q, 'selected_bg': bg, 'blood_groups': blood_groups
    })


@role_required('admin')
def admin_camps(request):
    if request.method == 'POST':
        form = CampForm(request.POST)
        if form.is_valid():
            camp = form.save(commit=False)
            camp.created_by = request.user
            camp.save()
            messages.success(request, '✅ Camp created successfully!')
            return redirect('admin_camps')
    else:
        form = CampForm()

    if 'status' in request.GET:
        camp = get_object_or_404(Camp, pk=request.GET.get('id'))
        camp.status = request.GET['status']
        camp.save()
        return redirect('admin_camps')

    camps = Camp.objects.all().order_by('-camp_date')
    return render(request, 'admin_panel/camps.html', {'camps': camps, 'form': form})


@role_required('admin')
def admin_hospitals(request):
    if 'verify' in request.GET:
        h = get_object_or_404(Hospital, pk=request.GET['verify'])
        h.verified = True
        h.save()
        messages.success(request, '✅ Hospital verified.')
        return redirect('admin_hospitals')
    if 'unverify' in request.GET:
        h = get_object_or_404(Hospital, pk=request.GET['unverify'])
        h.verified = False
        h.save()
        messages.warning(request, '⚠️ Verification revoked.')
        return redirect('admin_hospitals')

    hospitals = Hospital.objects.select_related('user').annotate(
        total_requests=Count('user__blood_requests'),
        fulfilled_count=Count('user__blood_requests', filter=Q(user__blood_requests__status='fulfilled'))
    )
    return render(request, 'admin_panel/hospitals.html', {'hospitals': hospitals})


@role_required('admin')
def admin_reports(request):
    # ── Monthly donations — works on BOTH MySQL and PostgreSQL ──
    six_months_ago = date.today() - timedelta(days=180)
    approved_donations = Donation.objects.filter(
        status='approved',
        donation_date__gte=six_months_ago
    ).order_by('donation_date')

    # Build monthly summary in Python (DB-agnostic)
    monthly_map = {}
    for d in approved_donations:
        key = d.donation_date.strftime('%b %Y')
        if key not in monthly_map:
            monthly_map[key] = {'month': key, 'count': 0, 'total_units': 0}
        monthly_map[key]['count']       += 1
        monthly_map[key]['total_units'] += float(d.units_donated)
    monthly = list(monthly_map.values())

    by_group = (
        Donation.objects.filter(status='approved')
        .values('blood_group')
        .annotate(count=Count('id'), total_units=Sum('units_donated'))
        .order_by('-total_units')
    )
    req_stats  = BloodRequest.objects.values('status').annotate(count=Count('id'))
    top_donors = Donor.objects.select_related('user').order_by('-total_donations')[:10]

    context = {
        'monthly':         monthly,
        'by_group':        by_group,
        'req_stats':       req_stats,
        'top_donors':      top_donors,
        'total_approved':  Donation.objects.filter(status='approved').count(),
        'total_units_don': Donation.objects.filter(status='approved').aggregate(t=Sum('units_donated'))['t'] or 0,
        'total_fulfilled': BloodRequest.objects.filter(status='fulfilled').count(),
        'total_units_ful': BloodRequest.objects.filter(status='fulfilled').aggregate(t=Sum('units_needed'))['t'] or 0,
    }
    return render(request, 'admin_panel/reports.html', context)


# ══════════════════════════════════════════════════════════════
#  DONOR VIEWS
# ══════════════════════════════════════════════════════════════

@role_required('donor')
def donor_dashboard(request):
    donor     = get_object_or_404(Donor, user=request.user)
    donor.check_eligibility()
    donations = Donation.objects.filter(donor=donor).order_by('-donation_date')[:6]
    camps     = Camp.objects.filter(status='upcoming', camp_date__gte=date.today())[:4]
    inventory = BloodInventory.objects.all()
    return render(request, 'donor/dashboard.html', {
        'donor': donor, 'donations': donations,
        'camps': camps, 'inventory': inventory,
    })


@role_required('donor')
def donor_donate(request):
    donor = get_object_or_404(Donor, user=request.user)
    donor.check_eligibility()
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            if not donor.is_eligible:
                messages.error(request, '❌ You are not eligible to donate yet.')
            else:
                d = form.save(commit=False)
                d.donor = donor
                d.save()
                messages.success(request, '✅ Donation submitted! Admin will review and approve it.')
                return redirect('donor_dashboard')
    else:
        form = DonationForm(initial={'blood_group': donor.blood_group})
    return render(request, 'donor/donate.html', {'form': form, 'donor': donor})


@role_required('donor')
def donor_history(request):
    donor     = get_object_or_404(Donor, user=request.user)
    donations = Donation.objects.filter(donor=donor).select_related('camp')
    return render(request, 'donor/history.html', {'donor': donor, 'donations': donations})


@role_required('donor')
def donor_camps(request):
    donor = get_object_or_404(Donor, user=request.user)
    if 'register' in request.GET:
        camp = get_object_or_404(Camp, pk=request.GET['register'])
        if camp.registered_count < camp.capacity:
            _, created = CampRegistration.objects.get_or_create(camp=camp, donor=donor)
            if created:
                camp.registered_count += 1
                camp.save()
                messages.success(request, '✅ Registered for camp!')
            else:
                messages.warning(request, '⚠️ Already registered for this camp.')
        else:
            messages.error(request, '❌ This camp is full.')
        return redirect('donor_camps')

    camps   = Camp.objects.filter(status__in=['upcoming', 'ongoing']).order_by('camp_date')
    my_regs = CampRegistration.objects.filter(donor=donor).values_list('camp_id', flat=True)
    return render(request, 'donor/camps.html', {'camps': camps, 'my_regs': list(my_regs)})


@role_required('donor')
def donor_profile(request):
    donor = get_object_or_404(Donor, user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            weight = request.POST.get('weight_kg')
            if weight:
                donor.weight_kg = weight
                donor.save()
            messages.success(request, '✅ Profile updated!')
            return redirect('donor_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'donor/profile.html', {'form': form, 'donor': donor})


# ══════════════════════════════════════════════════════════════
#  HOSPITAL VIEWS
# ══════════════════════════════════════════════════════════════

@role_required('hospital')
def hospital_dashboard(request):
    hospital  = get_object_or_404(Hospital, user=request.user)
    my_reqs   = BloodRequest.objects.filter(requester=request.user).order_by('-request_date')[:8]
    inventory = BloodInventory.objects.all()
    return render(request, 'hospital/dashboard.html', {
        'hospital':  hospital,
        'my_reqs':   my_reqs,
        'inventory': inventory,
        'pending':   BloodRequest.objects.filter(requester=request.user, status='pending').count(),
        'fulfilled': BloodRequest.objects.filter(requester=request.user, status='fulfilled').count(),
        'total':     BloodRequest.objects.filter(requester=request.user).count(),
    })


@role_required('hospital')
def hospital_request(request):
    inventory = {inv.blood_group: inv.units_available for inv in BloodInventory.objects.all()}
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.requester = request.user
            req.save()
            messages.success(request, '✅ Blood request submitted! Admin will process it shortly.')
            return redirect('hospital_dashboard')
    else:
        form = BloodRequestForm()
    return render(request, 'hospital/request.html', {'form': form, 'inventory': inventory})


@role_required('hospital')
def hospital_my_requests(request):
    if 'cancel' in request.GET:
        req = get_object_or_404(BloodRequest, pk=request.GET['cancel'], requester=request.user)
        if req.status == 'pending':
            req.status = 'cancelled'
            req.save()
            messages.warning(request, '⚠️ Request cancelled.')
        return redirect('hospital_my_requests')

    status_filter = request.GET.get('s', '')
    qs = BloodRequest.objects.filter(requester=request.user)
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'hospital/my_requests.html', {'requests': qs, 'filter': status_filter})


@role_required('hospital')
def hospital_inventory(request):
    inventory = BloodInventory.objects.all()
    return render(request, 'hospital/inventory.html', {'inventory': inventory})
