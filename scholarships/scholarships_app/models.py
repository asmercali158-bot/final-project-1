from django.db import models
from django.contrib.auth.models import User

# --- 1. SCHOLARSHIP MODEL ---
class Scholarship(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    field = models.CharField(max_length=100) #
    min_gpa = models.FloatField() #
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- 2. PROFILE MODEL (Matching & Vault) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=True)
    gpa = models.FloatField(default=0.0) # Weighted Scoring
    interested_field = models.CharField(max_length=100, blank=True) # Matching
    preferred_country = models.CharField(max_length=100, blank=True) # Demographics
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    # Document Vault (Kaydka Dukumiintiyada)
    cv = models.FileField(upload_to='vault/cvs/', null=True, blank=True)
    transcript = models.FileField(upload_to='vault/transcripts/', null=True, blank=True)
    is_verified = models.BooleanField(default=False) # Verification System

    def __str__(self):
        return self.user.username

# --- 3. APPLICATION MODEL (Lifecycle) ---
class Application(models.Model):
    # States: Draft, Under Review, Accepted, Rejected
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Under Review', 'Under Review'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Under Review')
    applied_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Audit Trail

    def __str__(self):
        return f"{self.user.username} - {self.scholarship.title}"

# --- 4. NOTIFICATION MODEL (Real-Time Alerts) ---
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField() # Alerts & Deadlines
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To: {self.user.username} - {self.message[:20]}"

# --- 5. PAYMENT MODEL ---
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ${self.amount}"