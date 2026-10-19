from django.contrib import admin
from .models import CustomUser, Department, ProcurementMemo, ProcurementActionLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')
    list_filter = ('code',)
    search_fields = ('name',)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'department', 'account_approved', 'is_staff')
    list_filter = ('role', 'department', 'account_approved')


class ProcurementActionLogInLine(admin.TabularInline):
    model = ProcurementActionLog
    extra = 0
    readonly_fields = ('actor', 'actor_department', 'action', 'stage', 'comments', 'timestamp')


@admin.register(ProcurementMemo)
class ProcurementMemoAdmin(admin.ModelAdmin):
    list_display = ('title', 'originating_department', 'estimated_amount', 'final_voucher_amount', 'current_status', 'created_at')
    list_filter = ('current_status', 'originating_department')
    search_fields = ('title', 'description', 'voucher_number')
    inlines = [ProcurementActionLogInLine]


@admin.register(ProcurementActionLog)
class ProcurementActionLogAdmin(admin.ModelAdmin):
    list_display = ('memo', 'actor', 'actor_department', 'action', 'stage', 'timestamp')
    list_filter = ('action', 'stage', 'timestamp')