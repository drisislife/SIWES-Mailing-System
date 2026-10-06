from django.contrib import admin
from .models import CustomUser, Department, ProcurementMemo

# Make Departments show up in the admin panel
admin.site.register(Department)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'department', 'account_approved', 'is_staff')
    list_filter = ('role', 'department', 'account_approved')

@admin.register(ProcurementMemo)
class ProcurementMemoAdmin(admin.ModelAdmin):
    list_display = ('title', 'originating_department', 'current_status', 'created_at')
    list_filter = ('current_status', 'originating_department')