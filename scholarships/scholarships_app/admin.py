from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from .models import Profile, Scholarship, Application, Notification, Payment, Document, ApplicationLog


# ============================================================
# 1. PROFILE ADMIN
# ============================================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role_badge', 'gpa', 'interested_field', 'verification_status', 'preferred_country')
    list_editable = ('gpa',)
    list_filter = ('role', 'is_verified', 'interested_field', 'preferred_country')
    search_fields = ('user__username', 'full_name', 'user__email', 'interested_field')
    readonly_fields = ('user',)
    ordering = ('-is_verified', 'role')

    actions = ['verify_users', 'unverify_users', 'suspend_users']

    fieldsets = (
        ('👤 Macluumaadka Aasaasiga', {
            'fields': ('user', 'full_name', 'role', 'bio', 'profile_pic')
        }),
        ('🎓 Xogta Tacliinta', {
            'fields': ('gpa', 'interested_field', 'preferred_country', 'location')
        }),
        ('✅ Xaaladda', {
            'fields': ('is_verified',)
        }),
    )

    def role_badge(self, obj):
        colors = {'Admin': '#dc3545', 'Provider': '#0d6efd', 'Student': '#198754'}
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.role
        )
    role_badge.short_description = 'Role'

    def verification_status(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#198754">✅ Verified</span>')
        return format_html('<span style="color:#dc3545">❌ Pending</span>')
    verification_status.short_description = 'Xaqiijin'

    @admin.action(description='✅ Xaqiiji isticmaalayaasha la doortay')
    def verify_users(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} isticmaale waa la xaqiijiyay.')

    @admin.action(description='❌ Xaqiijinta ka saar')
    def unverify_users(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f'{count} isticmaale xaqiijintii waa laga saaray.')

    @admin.action(description='🚫 Suspend isticmaalayaasha la doortay')
    def suspend_users(self, request, queryset):
        count = 0
        for profile in queryset:
            if profile.user != request.user:
                profile.user.is_active = False
                profile.user.save()
                count += 1
        self.message_user(request, f'{count} account ayaa la xidday.')


# ============================================================
# 2. SCHOLARSHIP ADMIN
# ============================================================
@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'field', 'min_gpa', 'deadline', 'approval_status', 'created_at')
    list_filter = ('is_approved', 'field', 'deadline')
    search_fields = ('title', 'field', 'provider__username', 'description')
    date_hierarchy = 'deadline'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    actions = ['approve_scholarships', 'unapprove_scholarships']

    fieldsets = (
        ('📋 Macluumaadka Deeqda', {
            'fields': ('provider', 'title', 'description', 'field', 'location')
        }),
        ('📊 Shuruudaha', {
            'fields': ('min_gpa', 'deadline')
        }),
        ('⚖️ Matching Weights', {
            'fields': ('weight_gpa', 'weight_location', 'weight_field'),
            'classes': ('collapse',),
            'description': 'GPA + Location + Field = 100% noqon kara'
        }),
        ('✅ Maamul', {
            'fields': ('is_approved', 'created_at')
        }),
    )

    def approval_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color:#198754;font-weight:bold">✅ Approved</span>')
        return format_html('<span style="color:#ffc107;font-weight:bold">⏳ Pending Review</span>')
    approval_status.short_description = 'Xaaladda'

    @admin.action(description='✅ Ansixii deeqaha la doortay')
    def approve_scholarships(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f'{count} deeq waa la ansixiyay.')

    @admin.action(description='❌ Ansixinta ka saar')
    def unapprove_scholarships(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} deeq ansixintii waa laga saaray.')


# ============================================================
# 3. APPLICATION ADMIN
# ============================================================
class ApplicationLogInline(admin.TabularInline):
    model = ApplicationLog
    extra = 0
    readonly_fields = ('user', 'previous_status', 'new_status', 'timestamp')
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'scholarship', 'status_badge', 'match_score_display', 'applied_on', 'updated_at')
    list_filter = ('status', 'applied_on', 'scholarship__field')
    list_editable = ('status',)
    search_fields = ('user__username', 'scholarship__title')
    ordering = ('-applied_on',)
    inlines = [ApplicationLogInline]

    actions = ['accept_applications', 'reject_applications', 'set_under_review']

    def status_badge(self, obj):
        colors = {
            'Draft': '#6c757d',
            'Submitted': '#0d6efd',
            'Under Review': '#ffc107',
            'Accepted': '#198754',
            'Rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'

    def match_score_display(self, obj):
        score = obj.match_score
        if score >= 80:
            color = '#198754'
        elif score >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color:{};font-weight:bold">{}%</span>', color, int(score)
        )
    match_score_display.short_description = 'Match Score'

    @admin.action(description='✅ Codsiyada la doortay Accepted u bedel')
    def accept_applications(self, request, queryset):
        count = queryset.update(status='Accepted')
        self.message_user(request, f'{count} codsi waa la aqbalay.')

    @admin.action(description='❌ Codsiyada la doortay Rejected u bedel')
    def reject_applications(self, request, queryset):
        count = queryset.update(status='Rejected')
        self.message_user(request, f'{count} codsi waa la diiday.')

    @admin.action(description='🔍 Under Review u bedel')
    def set_under_review(self, request, queryset):
        count = queryset.update(status='Under Review')
        self.message_user(request, f'{count} codsi waa la eegayaa.')


# ============================================================
# 4. DOCUMENT ADMIN
# ============================================================
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'verification_badge', 'uploaded_at')
    list_filter = ('document_type', 'is_verified', 'uploaded_at')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'uploaded_at')
    actions = ['verify_documents']

    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color:#198754">✅ Verified</span>')
        return format_html('<span style="color:#dc3545">❌ Unverified</span>')
    verification_badge.short_description = 'Xaqiijin'

    @admin.action(description='✅ Xaqiiji documents-ka la doortay')
    def verify_documents(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} document waa la xaqiijiyay.')


# ============================================================
# 5. APPLICATION LOG ADMIN
# ============================================================
@admin.register(ApplicationLog)
class ApplicationLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'user', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('new_status', 'timestamp')
    search_fields = ('application__user__username', 'application__scholarship__title')
    readonly_fields = ('application', 'user', 'previous_status', 'new_status', 'timestamp')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False  # Logs si otomaatig ah ayaa loo abuuraa, gacanta kama samayso


# ============================================================
# 6. NOTIFICATION ADMIN
# ============================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'short_message', 'read_status', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_all_read']

    def short_message(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    short_message.short_description = 'Farriin'

    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#6c757d">Akhriyay</span>')
        return format_html('<span style="color:#0d6efd;font-weight:bold">Cusub</span>')
    read_status.short_description = 'Xaaladda'

    @admin.action(description='📖 La doortay u calaamadee "Akhriyay"')
    def mark_all_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} ogeysiis waa la akhriyay.')


# ============================================================
# 7. PAYMENT ADMIN
# ============================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'formatted_amount', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__username',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

    def formatted_amount(self, obj):
        return format_html('<span style="color:#198754;font-weight:bold">${}</span>', obj.amount)
    formatted_amount.short_description = 'Lacagta'


# ============================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================
admin.site.site_header = "🎓 ScholarSync Admin Panel"
admin.site.site_title = "ScholarSync"
admin.site.index_title = "Xarunta Maamulka"
