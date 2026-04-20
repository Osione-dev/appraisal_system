from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Appraisal


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'job_title')
    list_filter = ('role', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Team', {'fields': ('role', 'department', 'job_title', 'team_lead')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Team', {'fields': ('role', 'department', 'job_title', 'team_lead')}),
    )


@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'status', 'reviewed_by_lead', 'reviewed_by_hr', 'created_at')
    list_filter = ('status', 'period')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name', 'period')
    readonly_fields = ('created_at', 'updated_at', 'submitted_to_lead_at', 'submitted_to_hr_at', 'reviewed_at')
