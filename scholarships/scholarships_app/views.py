from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.http import HttpResponse
from .models import Scholarship, Profile, Application, Payment, Notification
from reportlab.pdfgen import canvas 
from django.db.models import Count, Sum, Q

# ========================================================
# 1. AUTH & LANDING
# ========================================================
def landing_page(request):
    """Bogga hore ee nidaamka ScholarAI"""
    return render(request, 'landing.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Account-kaaga si guul leh ayaa loo sameeyay!")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# ========================================================
# 2. STUDENT DASHBOARD & PROFILE
# ========================================================
@login_required
def dashboard_v20(request):
    """Elite Dashboard - Waxay muujisaa xogta ardayga ee lixda qodob"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    apps = Application.objects.filter(user=request.user).order_by('-applied_on')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    matches_count = Scholarship.objects.filter(
        Q(field__icontains=profile.interested_field) | Q(min_gpa__lte=profile.gpa)
    ).count()
    
    return render(request, 'dashboard.html', {
        'profile': profile, 
        'applications': apps, 
        'notifications': notifications,
        'matches': {'count': matches_count} 
    })

@login_required
def update_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.gpa = request.POST.get('gpa')
        profile.interested_field = request.POST.get('interested_field')
        profile.preferred_country = request.POST.get('preferred_country')
        profile.save()
        messages.success(request, "Profile-kaaga waa la cusubaysiiyay!")
        return redirect('dashboard')
    return render(request, 'profile_settings.html', {'profile': profile})

# ========================================================
# 3. MATCHING & DOCUMENTS (VAULT)
# ========================================================
@login_required
def matches_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    scholarships = Scholarship.objects.filter(
        Q(field__icontains=profile.interested_field) | Q(min_gpa__lte=profile.gpa)
    ).order_by('-min_gpa') 
    return render(request, 'matches.html', {'matches': scholarships, 'profile': profile})

@login_required
def document_vault_view(request):
    """Document Vault: Khubada 2aad (Verification System)"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if 'cv' in request.FILES: profile.cv = request.FILES['cv']
        if 'transcript' in request.FILES: profile.transcript = request.FILES['transcript']
        profile.save()
        messages.success(request, "Dukumiintiyada waa la xaqiijiyay (Verified).")
    return render(request, 'vault.html', {'profile': profile})

# ========================================================
# 4. APPLICATIONS, DETAILS & CHECKOUT
# ========================================================
@login_required
def scholarship_detail(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk)
    return render(request, 'scholarship_detail.html', {'scholarship': scholarship})

@login_required
def checkout(request, scholarship_id):
    """Bogga lacag bixinta ee deeqda"""
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    return render(request, 'checkout.html', {'scholarship': scholarship})

@login_required
def final_submission(request, scholarship_id):
    """Xallinta Attribute Error: final_submission"""
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    return render(request, 'final_review.html', {'scholarship': scholarship})

@login_required
def submit_application(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    app, created = Application.objects.get_or_create(
        user=request.user, 
        scholarship=scholarship,
        defaults={'status': 'Under Review'}
    )
    if created:
        Notification.objects.create(
            user=request.user,
            message=f"Codsigaaga {scholarship.title} waa la bilaabay (Under Review)."
        )
        messages.success(request, "Codsigaaga si guul leh ayaa loo gudbiyay.")
    return redirect('dashboard')

# ========================================================
# 5. ROLES & NOTIFICATIONS
# ========================================================
@user_passes_test(lambda u: u.is_staff or u.groups.filter(name='Provider').exists())
def provider_dashboard(request):
    apps = Application.objects.all().order_by('-applied_on')
    return render(request, 'provider_dashboard.html', {'apps': apps})

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifs})

# ========================================================
# 6. ADMIN ANALYTICS (ELITE CONTROL)
# ========================================================
@user_passes_test(lambda u: u.is_staff)
def admin_analytics(request):
    """Admin Dashboard: Khubada 6aad (Analytics & Reporting)"""
    total_students = Profile.objects.count()
    total_apps = Application.objects.count()
    accepted = Application.objects.filter(status='Accepted').count()
    
    success_rate = (accepted / total_apps * 100) if total_apps > 0 else 0
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_verifications = Profile.objects.filter(is_verified=False).count()
    
    recent_logs = Application.objects.select_related('user', 'scholarship').all().order_by('-applied_on')[:5]
    stats = Profile.objects.values('preferred_country').annotate(count=Count('id'))
    
    return render(request, 'admin_stats.html', {
        'total_students': total_students,
        'total_applications': total_apps,
        'success_rate': round(success_rate, 1),
        'total_revenue': total_revenue,
        'pending_verifications': pending_verifications,
        'recent_logs': recent_logs,
        'stats': stats
    })

# ========================================================
# 7. PAYMENTS & PDF RECEIPTS
# ========================================================
@login_required
def download_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.id}.pdf"'
    p = canvas.Canvas(response)
    p.drawString(100, 800, "ScholarAI Official Receipt")
    p.drawString(100, 750, f"Student: {payment.user.username}")
    p.drawString(100, 730, f"Amount Paid: ${payment.amount}")
    p.showPage()
    p.save()
    return response