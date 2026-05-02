from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # --- 1. LANDING & AUTH ---
    path('', views.landing_page, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # --- 2. SCHOLARAI CORE (Dashboard & Matching) ---
    path('dashboard/', views.dashboard_v20, name='dashboard'),
    path('matches/', views.matches_view, name='matches'), 
    path('scholarship/<int:pk>/', views.scholarship_detail, name='scholarship_detail'),
    
    # --- 3. PROFILE & DOCUMENT VAULT ---
    path('profile/update/', views.update_profile, name='update_profile'),
    path('vault/', views.document_vault_view, name='vault'), 
    
    # --- 4. APPLICATION LIFECYCLE & PAYMENTS ---
    path('checkout/<int:scholarship_id>/', views.checkout, name='checkout'),
    path('final-review/<int:scholarship_id>/', views.final_submission, name='final_review'), 
    path('apply/<int:scholarship_id>/', views.submit_application, name='submit_application'),
    path('download-receipt/<int:payment_id>/', views.download_receipt, name='download_receipt'),
    
    # --- 5. REAL-TIME NOTIFICATIONS ---
    path('notifications/', views.notifications_view, name='notifications'), 
    
    # --- 6. ROLE-BASED ACCESS ---
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'), 
    
    # --- 7. ADMIN ANALYTICS ---
    # Waxaan u beddelnay 'admin_stats' si uu ula jaanqaado template-kaaga
    path('admin-stats/', views.admin_analytics, name='admin_stats'), 
]

# Tani waxay muhiim u tahay in Dukumiintiyada (CV/Transcripts) lagu arki karo browser-ka
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)