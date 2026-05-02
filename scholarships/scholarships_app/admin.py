from django.contrib import admin
from .models import Profile, Scholarship, Application, Notification, Payment

# 1. PROFILE ADMIN (Maamulka Isticmaalayaasha & Verification)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Waxaan u beddelnay is_verified si loo waafajiyo Verification System-ka
    list_display = ('user', 'full_name', 'gpa', 'interested_field', 'is_verified', 'preferred_country')
    list_editable = ('is_verified', 'gpa') # Si fudud u xaqiiji ardayga (Verify)
    search_fields = ('user__username', 'full_name', 'interested_field')
    list_filter = ('is_verified', 'interested_field', 'preferred_country')

# 2. SCHOLARSHIP ADMIN (Maamulka Deeqaha)
@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    # Waxaan saxnay field-yada si ay ula mid noqdaan models.py (min_gpa, field)
    list_display = ('title', 'field', 'min_gpa', 'deadline', 'created_at')
    search_fields = ('title', 'field')
    list_filter = ('field',) # Halkan waa laga saaray 'country' sababtoo ah moodalka kuma jiro
    date_hierarchy = 'deadline'
    ordering = ('deadline',)

# 3. APPLICATION ADMIN (Socodka Codsiga & Audit Trail)
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Waxaan ku darnay updated_at si loo helo Audit Trail
    list_display = ('user', 'scholarship', 'status', 'applied_on', 'updated_at')
    list_filter = ('status', 'applied_on')
    list_editable = ('status',) # Admin-ku halkan ayuu ka beddelayaa Accepted/Rejected
    search_fields = ('user__username', 'scholarship__title')

# 4. NOTIFICATION ADMIN (Ogeysiisyada Tooska ah)
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')

# 5. PAYMENT ADMIN (Dhaqdhaqaaqa Lacagta)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'timestamp')