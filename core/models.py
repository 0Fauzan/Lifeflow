from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ─── CUSTOM USER MODEL ────────────────────────────────────────
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',    'Admin'),
        ('donor',    'Donor'),
        ('hospital', 'Hospital'),
    ]
    role    = models.CharField(max_length=10, choices=ROLE_CHOICES, default='donor')
    phone   = models.CharField(max_length=15, blank=True, null=True)
    city    = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):    return self.role == 'admin'
    @property
    def is_donor(self):    return self.role == 'donor'
    @property
    def is_hospital(self): return self.role == 'hospital'


# ─── DONOR PROFILE ────────────────────────────────────────────
class Donor(models.Model):
    BLOOD_GROUPS = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    GENDER_CHOICES = [('Male','Male'),('Female','Female'),('Other','Other')]

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    blood_group     = models.CharField(max_length=5, choices=BLOOD_GROUPS)
    dob             = models.DateField()
    gender          = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    weight_kg       = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    last_donation   = models.DateField(blank=True, null=True)
    is_eligible     = models.BooleanField(default=True)
    total_donations = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.blood_group}"

    def check_eligibility(self):
        if self.last_donation:
            days = (timezone.now().date() - self.last_donation).days
            self.is_eligible = days >= 90
            self.save(update_fields=['is_eligible'])
        return self.is_eligible

    @property
    def next_eligible_date(self):
        if self.last_donation:
            from datetime import timedelta
            return self.last_donation + timedelta(days=90)
        return None


# ─── HOSPITAL PROFILE ─────────────────────────────────────────
class Hospital(models.Model):
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_profile')
    hospital_name = models.CharField(max_length=200)
    license_no    = models.CharField(max_length=100, unique=True, blank=True, null=True)
    verified      = models.BooleanField(default=False)

    def __str__(self):
        return self.hospital_name


# ─── BLOOD INVENTORY ──────────────────────────────────────────
class BloodInventory(models.Model):
    BLOOD_GROUPS = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    blood_group     = models.CharField(max_length=5, choices=BLOOD_GROUPS, unique=True)
    units_available = models.IntegerField(default=0)
    last_updated    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_group}: {self.units_available} units"

    @property
    def stock_status(self):
        if self.units_available == 0:   return 'Out of Stock'
        if self.units_available < 5:    return 'Critical'
        if self.units_available < 20:   return 'Low'
        return 'Adequate'

    @property
    def status_class(self):
        return {
            'Adequate':     'adequate',
            'Low':          'low',
            'Critical':     'critical',
            'Out of Stock': 'empty',
        }.get(self.stock_status, 'empty')

    class Meta:
        verbose_name_plural = 'Blood Inventory'


# ─── DONATION CAMP ────────────────────────────────────────────
class Camp(models.Model):
    STATUS_CHOICES = [
        ('upcoming','Upcoming'),('ongoing','Ongoing'),
        ('completed','Completed'),('cancelled','Cancelled'),
    ]
    name             = models.CharField(max_length=200)
    location         = models.TextField()
    city             = models.CharField(max_length=100, blank=True)
    camp_date        = models.DateField()
    start_time       = models.TimeField(blank=True, null=True)
    end_time         = models.TimeField(blank=True, null=True)
    organizer        = models.CharField(max_length=150, blank=True)
    capacity         = models.IntegerField(default=100)
    registered_count = models.IntegerField(default=0)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.camp_date}"

    class Meta:
        ordering = ['-camp_date']


# ─── CAMP REGISTRATION ────────────────────────────────────────
class CampRegistration(models.Model):
    camp          = models.ForeignKey(Camp, on_delete=models.CASCADE, related_name='registrations')
    donor         = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='camp_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended      = models.BooleanField(default=False)

    class Meta:
        unique_together = ('camp', 'donor')

    def __str__(self):
        return f"{self.donor.user.get_full_name()} @ {self.camp.name}"


# ─── DONATION ─────────────────────────────────────────────────
class Donation(models.Model):
    BLOOD_GROUPS = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    STATUS_CHOICES = [
        ('pending','Pending'),('approved','Approved'),('rejected','Rejected'),
    ]
    donor         = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    blood_group   = models.CharField(max_length=5, choices=BLOOD_GROUPS)
    units_donated = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    donation_date = models.DateField()
    camp          = models.ForeignKey(Camp, on_delete=models.SET_NULL, null=True, blank=True)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes         = models.TextField(blank=True)
    approved_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_donations')
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.get_full_name()} — {self.blood_group} on {self.donation_date}"

    class Meta:
        ordering = ['-donation_date']


# ─── BLOOD REQUEST ────────────────────────────────────────────
class BloodRequest(models.Model):
    BLOOD_GROUPS = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    URGENCY_CHOICES = [
        ('low','Low'),('medium','Medium'),('high','High'),('critical','Critical'),
    ]
    STATUS_CHOICES = [
        ('pending','Pending'),('approved','Approved'),
        ('fulfilled','Fulfilled'),('rejected','Rejected'),('cancelled','Cancelled'),
    ]
    requester      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blood_requests')
    patient_name   = models.CharField(max_length=100)
    blood_group    = models.CharField(max_length=5, choices=BLOOD_GROUPS)
    units_needed   = models.DecimalField(max_digits=5, decimal_places=2)
    urgency        = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    reason         = models.TextField(blank=True)
    status         = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    request_date   = models.DateTimeField(auto_now_add=True)
    fulfilled_date = models.DateField(blank=True, null=True)
    handled_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_requests')

    def __str__(self):
        return f"{self.patient_name} needs {self.blood_group} — {self.urgency}"

    class Meta:
        ordering = ['-request_date']

    URGENCY_ORDER = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}


# ─── NOTIFICATION ─────────────────────────────────────────────
class Notification(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.user.username}] {self.title}"

    class Meta:
        ordering = ['-created_at']
