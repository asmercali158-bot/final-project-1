from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Scholarship, Profile, Application, Payment, Notification, Document, ApplicationLog
from reportlab.pdfgen import canvas


# ============================================================
# HELPERS
# ============================================================
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'Admin'

def is_provider(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'Provider'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'Student'

def calculate_match_score(profile, scholarship):
    """Matching Engine: GPA 50% + Location 30% + Field 20%"""
    score = 0
    if profile.gpa >= scholarship.min_gpa:
        score += scholarship.weight_gpa
    if profile.location and scholarship.location:
        if profile.location.strip().lower() == scholarship.location.strip().lower():
            score += scholarship.weight_location
    if profile.interested_field and scholarship.field:
        if profile.interested_field.strip().lower() == scholarship.field.strip().lower():
            score += scholarship.weight_field
    return min(score, 100)


# ============================================================
# 1. AUTH & LANDING
# ============================================================
def landing_page(request):
    total_scholarships = Scholarship.objects.filter(is_approved=True).count()
    total_students = Profile.objects.filter(role='Student').count()
    context = {
        'total_scholarships': total_scholarships,
        'total_students': total_students,
    }
    return render(request, 'landing_page.html', context)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        role = request.POST.get('role', 'Student')
        if form.is_valid():
            user = form.save()
            # Profile-ka si otomaatig ah u samee
            Profile.objects.get_or_create(user=user, defaults={'role': role})
            auth_login(request, user)
            messages.success(request, "Account-kaaga si guul leh ayaa loo sameeyay!")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


# ============================================================
# 2. STUDENT DASHBOARD & PROFILE
# ============================================================
@login_required
def dashboard_v20(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Role-based redirect
    if profile.role == 'Admin':
        return redirect('admin_stats')
    if profile.role == 'Provider':
        return redirect('provider_dashboard')

    apps = Application.objects.filter(user=request.user).select_related('scholarship').order_by('-applied_on')
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]

    # Approved deeqaha oo keliya
    approved_scholarships = Scholarship.objects.filter(is_approved=True)
    matches_count = approved_scholarships.filter(
        Q(field__icontains=profile.interested_field) | Q(min_gpa__lte=profile.gpa)
    ).count()

    # Stats
    accepted_count = apps.filter(status='Accepted').count()
    pending_count = apps.filter(status__in=['Submitted', 'Under Review']).count()

    return render(request, 'dashboard.html', {
        'profile': profile,
        'applications': apps,
        'notifications': notifications,
        'matches': {'count': matches_count},
        'accepted_count': accepted_count,
        'pending_count': pending_count,
        'total_apps': apps.count(),
    })


@login_required
def update_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '').strip()
        profile.bio = request.POST.get('bio', '').strip()
        profile.location = request.POST.get('location', '').strip()
        profile.interested_field = request.POST.get('interested_field', '').strip()
        profile.preferred_country = request.POST.get('preferred_country', '').strip()

        gpa_raw = request.POST.get('gpa', '0')
        try:
            gpa = float(gpa_raw)
            if 0.0 <= gpa <= 4.0:
                profile.gpa = gpa
            else:
                messages.error(request, "GPA-gu waa inuu u dhexeeyaa 0.0 iyo 4.0")
                return render(request, 'profile_settings.html', {'profile': profile})
        except ValueError:
            messages.error(request, "GPA xog khaldan ayaa la geliyay.")
            return render(request, 'profile_settings.html', {'profile': profile})

        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']

        profile.save()
        messages.success(request, "Profile-kaaga waa la cusboonaysiiyay!")
        return redirect('dashboard')
    return render(request, 'profile_settings.html', {'profile': profile})


# ============================================================
# 3. MATCHING ENGINE & DOCUMENT VAULT
# ============================================================
@login_required
def matches_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    approved = Scholarship.objects.filter(is_approved=True)

    # Xisaabi score-ka deeq kasta
    matched = []
    for s in approved:
        score = calculate_match_score(profile, s)
        if score > 0:
            matched.append({'scholarship': s, 'score': score})

    # Sort by score (highest first)
    matched.sort(key=lambda x: x['score'], reverse=True)

    return render(request, 'matches.html', {
        'matches': matched,
        'profile': profile,
    })


@login_required
def document_vault_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')

    if request.method == 'POST':
        doc_type = request.POST.get('document_type', 'Other')
        if 'file' in request.FILES:
            Document.objects.create(
                user=request.user,
                document_type=doc_type,
                file=request.FILES['file'],
            )
            messages.success(request, f"Dukumiintiga ({doc_type}) si guul leh ayaa loo keydiyay.")
            return redirect('vault')
        else:
            messages.error(request, "Fadlan file-ka dooro.")

    return render(request, 'vault.html', {
        'profile': profile,
        'documents': documents,
    })


@login_required
@require_POST
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id, user=request.user)
    doc.delete()
    messages.success(request, "Dukumiintigii waa la tiriyay.")
    return redirect('vault')


# ============================================================
# 4. SCHOLARSHIP DETAIL, APPLICATION & CHECKOUT
# ============================================================
@login_required
def scholarship_detail(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, is_approved=True)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    score = calculate_match_score(profile, scholarship)
    already_applied = Application.objects.filter(user=request.user, scholarship=scholarship).exists()
    return render(request, 'scholarship_detail.html', {
        'scholarship': scholarship,
        'score': score,
        'already_applied': already_applied,
    })


@login_required
def checkout(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id, is_approved=True)
    return render(request, 'checkout.html', {'scholarship': scholarship})


@login_required
def final_submission(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    return render(request, 'final_review.html', {'scholarship': scholarship})


@login_required
def submit_application(request, scholarship_id):
    scholarship = get_object_or_404(Scholarship, id=scholarship_id, is_approved=True)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Hubi in deadline-ku uusan dhaafin
    if scholarship.deadline < timezone.now().date():
        messages.error(request, "Waqtiga codsiga waa dhaafay. Ma codsankarid deeqdaan.")
        return redirect('scholarship_detail', pk=scholarship_id)

    # Hubi in profile-ku buuxa yahay
    if not profile.gpa or not profile.interested_field:
        messages.warning(request, "Fadlan profile-kaaga dhamaystir (GPA + Field) kahor codsashada.")
        return redirect('update_profile')

    app, created = Application.objects.get_or_create(
        user=request.user,
        scholarship=scholarship,
        defaults={
            'status': 'Submitted',
            'match_score': calculate_match_score(profile, scholarship),
        }
    )

    if created:
        # Log + Notification
        ApplicationLog.objects.create(
            application=app,
            user=request.user,
            previous_status='',
            new_status='Submitted',
        )
        Notification.objects.create(
            user=request.user,
            notification_type='Status Update',
            message=f"Codsigaaga '{scholarship.title}' waa la gudbiyay. Xaaladdu: Submitted.",
        )
        messages.success(request, "Codsigaaga si guul leh ayaa loo gudbiyay!")
    else:
        messages.info(request, "Deeqdaan horay baad u codsatay.")

    return redirect('dashboard')


# ============================================================
# 5. NOTIFICATIONS
# ============================================================
@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


# ============================================================
# 6. PROVIDER DASHBOARD (Role-Based)
# ============================================================
@login_required
@user_passes_test(is_provider, login_url='/dashboard/')
def provider_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    my_scholarships = Scholarship.objects.filter(provider=request.user).order_by('-created_at')
    applications = Application.objects.filter(
        scholarship__provider=request.user
    ).select_related('user', 'scholarship').order_by('-applied_on')

    # Stats
    total_apps = applications.count()
    accepted = applications.filter(status='Accepted').count()
    pending = applications.filter(status__in=['Submitted', 'Under Review']).count()

    return render(request, 'provider_dashboard.html', {
        'profile': profile,
        'my_scholarships': my_scholarships,
        'applications': applications,
        'total_apps': total_apps,
        'accepted': accepted,
        'pending': pending,
    })


@login_required
@user_passes_test(is_provider, login_url='/dashboard/')
def provider_add_scholarship(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        field = request.POST.get('field', '').strip()
        location = request.POST.get('location', '').strip()
        min_gpa = request.POST.get('min_gpa', 0)
        deadline = request.POST.get('deadline')

        if not all([title, description, field, deadline]):
            messages.error(request, "Dhammaan meelaha lagama maarmaan ah buuxi.")
            return render(request, 'provider_add_scholarship.html')

        Scholarship.objects.create(
            provider=request.user,
            title=title,
            description=description,
            field=field,
            location=location,
            min_gpa=float(min_gpa),
            deadline=deadline,
            is_approved=False,  # Admin review lagama maarmaan
        )
        messages.success(request, "Deeqda waa la gudbiyay. Admin-ka ayaa dib u eegaya.")
        return redirect('provider_dashboard')

    return render(request, 'provider_add_scholarship.html')


@login_required
@user_passes_test(is_provider, login_url='/dashboard/')
def provider_update_application_status(request, app_id):
    """Provider-ku wuxuu bedeli karaa status-ka codsiga deeqdiisa"""
    app = get_object_or_404(Application, id=app_id, scholarship__provider=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            old_status = app.status
            app.status = new_status
            app.save()

            # Log the change
            ApplicationLog.objects.create(
                application=app,
                user=request.user,
                previous_status=old_status,
                new_status=new_status,
            )
            # Notify the student
            Notification.objects.create(
                user=app.user,
                notification_type='Status Update',
                message=f"Codsigaaga '{app.scholarship.title}' waa la cusboonaysiiyay. Hadda: {new_status}.",
            )
            messages.success(request, f"Xaaladda codsiga waa la beddelay: {new_status}")
    return redirect('provider_dashboard')


# ============================================================
# 7. ADMIN VIEWS (Full Control)
# ============================================================
@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_analytics(request):
    """Admin Dashboard: Analytics & Reporting"""
    # Core stats
    total_students = Profile.objects.filter(role='Student').count()
    total_providers = Profile.objects.filter(role='Provider').count()
    total_apps = Application.objects.count()
    accepted = Application.objects.filter(status='Accepted').count()
    success_rate = round((accepted / total_apps * 100), 1) if total_apps > 0 else 0
    total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    pending_verifications = Profile.objects.filter(is_verified=False, role='Student').count()
    pending_scholarships = Scholarship.objects.filter(is_approved=False).count()

    # Recent activity
    recent_logs = Application.objects.select_related('user', 'scholarship').order_by('-applied_on')[:10]

    # Geographic distribution
    geo_stats = Profile.objects.filter(role='Student').values('preferred_country').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Application status breakdown
    status_breakdown = Application.objects.values('status').annotate(count=Count('id'))

    # Monthly applications (last 6 months)
    avg_match = Application.objects.aggregate(Avg('match_score'))['match_score__avg'] or 0

    return render(request, 'admin_analytics.html', {
        'total_students': total_students,
        'total_providers': total_providers,
        'total_applications': total_apps,
        'success_rate': success_rate,
        'total_revenue': total_revenue,
        'pending_verifications': pending_verifications,
        'pending_scholarships': pending_scholarships,
        'recent_logs': recent_logs,
        'geo_stats': geo_stats,
        'status_breakdown': status_breakdown,
        'avg_match_score': round(avg_match, 1),
    })


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_users(request):
    """Admin: Maamulka isticmaalayaasha oo dhan"""
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users = Profile.objects.select_related('user').all()
    if search:
        users = users.filter(
            Q(user__username__icontains=search) | Q(full_name__icontains=search) | Q(user__email__icontains=search)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'admin_users.html', {
        'users': users,
        'search': search,
        'role_filter': role_filter,
    })


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_verify_user(request, user_id):
    """Admin: User-ka xaqiiji (Verify)"""
    profile = get_object_or_404(Profile, user__id=user_id)
    profile.is_verified = not profile.is_verified  # Toggle
    profile.save()
    status_text = "xaqiijiyay" if profile.is_verified else "xaqiijinta ka saaray"
    messages.success(request, f"User-ka {profile.user.username} ayaad {status_text}.")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_suspend_user(request, user_id):
    """Admin: User-ka suspend gee (is_active = False)"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "Naftaada ma suspend garayso!")
        return redirect('admin_users')
    target_user.is_active = not target_user.is_active
    target_user.save()
    action = "xidday" if not target_user.is_active else "xidka ka furay"
    messages.success(request, f"Account-ka {target_user.username} ayaad {action}.")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_scholarships(request):
    """Admin: Dhammaan deeqaha + Approve/Reject"""
    scholarships = Scholarship.objects.select_related('provider').order_by('-created_at')
    pending = scholarships.filter(is_approved=False)
    approved = scholarships.filter(is_approved=True)
    return render(request, 'admin_scholarships.html', {
        'pending': pending,
        'approved': approved,
    })


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_approve_scholarship(request, scholarship_id):
    """Admin: Deeqda ansix (Approve)"""
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    scholarship.is_approved = True
    scholarship.save()
    # Provider-ka u ogeysi
    if scholarship.provider:
        Notification.objects.create(
            user=scholarship.provider,
            notification_type='Verification',
            message=f"Deeqdaada '{scholarship.title}' Admin-ka ayaa ansixiyay. Hadda ardaydu waxay codsankaraan.",
        )
    messages.success(request, f"Deeqda '{scholarship.title}' waa la ansixiyay.")
    return redirect('admin_scholarships')


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_delete_scholarship(request, scholarship_id):
    """Admin: Deeqda been abuurka ah tiri"""
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)
    title = scholarship.title
    scholarship.delete()
    messages.success(request, f"Deeqda '{title}' waa la tiriyay.")
    return redirect('admin_scholarships')


@login_required
@user_passes_test(is_admin, login_url='/dashboard/')
def admin_audit_logs(request):
    """Admin: Audit Trail - dhammaan beddelada"""
    logs = ApplicationLog.objects.select_related(
        'application__user', 'application__scholarship', 'user'
    ).order_by('-timestamp')[:100]
    return render(request, 'admin_audit_logs.html', {'logs': logs})


# ============================================================
# 8. PAYMENTS & PDF RECEIPTS
# ============================================================
@login_required
def download_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.id}.pdf"'
    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "ScholarSync - Official Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Receipt ID: {payment.id}")
    p.drawString(100, 740, f"Student: {payment.user.username}")
    p.drawString(100, 720, f"Amount Paid: ${payment.amount}")
    p.drawString(100, 700, f"Date: {payment.timestamp.strftime('%Y-%m-%d %H:%M')}")
    p.showPage()
    p.save()
    return response


# ============================================================
# 9. REST API VIEWSETS (JWT Protected)
# ============================================================
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ScholarshipSerializer, ApplicationSerializer,
    DocumentSerializer, ProfileSerializer,
    UserSerializer, NotificationSerializer
)
from .permissions import IsAdminRole, IsProviderRole, IsStudentRole, IsOwnerOrAdmin


class RegisterAPIView(APIView):
    """API: User cusub samee + JWT token soo celi"""
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        role = request.data.get('role', 'Student')

        if not username or not password:
            return Response({'error': 'Username iyo password lagama maarmaan'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username horeba loo isticmaalay'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        Profile.objects.create(user=user, role=role)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User si guul leh ayaa loo abuuray',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': role,
        }, status=201)


class ProfileAPIView(APIView):
    """API: Profile-ka qofka logged in"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ScholarshipViewSet(viewsets.ModelViewSet):
    """API: Deeqaha - Provider ayaa ku dari karaa, Admin ayaa ansixiya"""
    queryset = Scholarship.objects.filter(is_approved=True)
    serializer_class = ScholarshipSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [(IsProviderRole | IsAdminRole)()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.role == 'Admin':
                return Scholarship.objects.all()
            elif user.profile.role == 'Provider':
                return Scholarship.objects.filter(provider=user)
        return Scholarship.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user, is_approved=False)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_matches(self, request):
        """API: Ardayga u qalma deeqaha (Matching Engine)"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        scholarships = Scholarship.objects.filter(is_approved=True)
        result = []
        for s in scholarships:
            score = calculate_match_score(profile, s)
            if score > 0:
                data = ScholarshipSerializer(s).data
                data['match_score'] = score
                result.append(data)
        result.sort(key=lambda x: x['match_score'], reverse=True)
        return Response(result)


class ApplicationViewSet(viewsets.ModelViewSet):
    """API: Codsiyada - Student ayaa codsada, Provider/Admin ayaa maamusha"""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsStudentRole()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.role == 'Admin':
                return Application.objects.all().select_related('user', 'scholarship')
            elif user.profile.role == 'Provider':
                return Application.objects.filter(scholarship__provider=user).select_related('user', 'scholarship')
        return Application.objects.filter(user=user).select_related('scholarship')

    def perform_create(self, serializer):
        scholarship = serializer.validated_data['scholarship']
        profile = self.request.user.profile

        # Hubi deadline
        if scholarship.deadline < timezone.now().date():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Waqtiga codsiga waa dhaafay.")

        score = calculate_match_score(profile, scholarship)
        app = serializer.save(user=self.request.user, match_score=score, status='Submitted')

        # Log + Notification
        ApplicationLog.objects.create(
            application=app, user=self.request.user,
            previous_status='', new_status='Submitted',
        )
        Notification.objects.create(
            user=self.request.user,
            notification_type='Status Update',
            message=f"Codsigaaga '{scholarship.title}' waa la gudbiyay.",
        )

    @action(detail=True, methods=['patch'], permission_classes=[IsProviderRole | IsAdminRole])
    def update_status(self, request, pk=None):
        """API: Provider/Admin ayaa status-ka beddelaya"""
        app = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response({'error': 'Status aan sax ahayn'}, status=400)

        old_status = app.status
        app.status = new_status
        app.save()

        ApplicationLog.objects.create(
            application=app, user=request.user,
            previous_status=old_status, new_status=new_status,
        )
        Notification.objects.create(
            user=app.user,
            notification_type='Status Update',
            message=f"Codsigaaga '{app.scholarship.title}' waa la cusboonaysiiyay. Hadda: {new_status}.",
        )
        return Response({'message': f'Status waa la beddelay: {new_status}'})


class DocumentViewSet(viewsets.ModelViewSet):
    """API: Document Vault - Ardayga ayaa documents-kiisa maamusha"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'Admin':
            return Document.objects.all()
        return Document.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationAPIView(APIView):
    """API: Ogeysiisyada - list + mark as read"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
        serializer = NotificationSerializer(notifs, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Mark all as read"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Dhammaan ogeysiisyada waa la akhriyay.'})
