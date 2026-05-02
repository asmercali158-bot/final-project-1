from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# ============================================================
# REST API ROUTER
# ============================================================
router = DefaultRouter()
router.register(r'scholarships', views.ScholarshipViewSet, basename='scholarship')
router.register(r'applications', views.ApplicationViewSet, basename='application')
router.register(r'documents', views.DocumentViewSet, basename='document')

urlpatterns = [

    # --------------------------------------------------------
    # REST API ENDPOINTS
    # --------------------------------------------------------
    path('api/', include(router.urls)),
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', views.ProfileAPIView.as_view(), name='api_profile'),
    path('api/notifications/', views.NotificationAPIView.as_view(), name='api_notifications'),

    # --------------------------------------------------------
    # 1. LANDING & AUTH
    # --------------------------------------------------------
    path('', views.landing_page, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # --------------------------------------------------------
    # 2. STUDENT (Dashboard, Matching, Profile)
    # --------------------------------------------------------
    path('dashboard/', views.dashboard_v20, name='dashboard'),
    path('matches/', views.matches_view, name='matches'),
    path('scholarship/<int:pk>/', views.scholarship_detail, name='scholarship_detail'),
    path('profile/update/', views.update_profile, name='update_profile'),

    # --------------------------------------------------------
    # 3. DOCUMENT VAULT
    # --------------------------------------------------------
    path('vault/', views.document_vault_view, name='vault'),
    path('vault/delete/<int:doc_id>/', views.delete_document, name='delete_document'),

    # --------------------------------------------------------
    # 4. APPLICATION LIFECYCLE & PAYMENTS
    # --------------------------------------------------------
    path('checkout/<int:scholarship_id>/', views.checkout, name='checkout'),
    path('final-review/<int:scholarship_id>/', views.final_submission, name='final_review'),
    path('apply/<int:scholarship_id>/', views.submit_application, name='submit_application'),
    path('download-receipt/<int:payment_id>/', views.download_receipt, name='download_receipt'),

    # --------------------------------------------------------
    # 5. NOTIFICATIONS
    # --------------------------------------------------------
    path('notifications/', views.notifications_view, name='notifications'),

    # --------------------------------------------------------
    # 6. PROVIDER VIEWS
    # --------------------------------------------------------
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('provider/scholarship/add/', views.provider_add_scholarship, name='provider_add_scholarship'),
    path('provider/application/<int:app_id>/status/', views.provider_update_application_status, name='provider_update_status'),

    # --------------------------------------------------------
    # 7. ADMIN VIEWS
    # --------------------------------------------------------
    path('admin-stats/', views.admin_analytics, name='admin_stats'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/verify/', views.admin_verify_user, name='admin_verify_user'),
    path('admin/users/<int:user_id>/suspend/', views.admin_suspend_user, name='admin_suspend_user'),
    path('admin/scholarships/', views.admin_scholarships, name='admin_scholarships'),
    path('admin/scholarships/<int:scholarship_id>/approve/', views.admin_approve_scholarship, name='admin_approve_scholarship'),
    path('admin/scholarships/<int:scholarship_id>/delete/', views.admin_delete_scholarship, name='admin_delete_scholarship'),
    path('admin/audit-logs/', views.admin_audit_logs, name='admin_audit_logs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
