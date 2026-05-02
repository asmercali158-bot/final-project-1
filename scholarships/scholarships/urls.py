from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin Interface
    path('admin/', admin.site.urls),

    # 2. App-kaaga ugu muhiimsan
    # Hubi in 'scholarships_app' ay tahay magaca galka app-kaaga
    path('', include('scholarships_app.urls')), 
]

# 3. Media & Static Configuration
# Tani waa lagama maarmaan si sawirrada profile-ka (Media) 
# iyo style-ka (CSS/JS) ay u shaqeeyaan xilliga development-ka.
if settings.DEBUG:
    # Serving Static files (CSS, JavaScript, Images)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Serving Media files (User uploaded documents, Profile pictures)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 4. Error Pages (Optional: Waxaad ku dari kartaa hadhow)
# handler404 = 'scholarships_app.views.error_404'