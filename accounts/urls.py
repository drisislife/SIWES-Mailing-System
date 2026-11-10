from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('directory/', views.staff_directory_view, name='staff_directory'),
    path('two-factor-verify/', views.two_factor_verify_view, name='two_factor_verify'),

    # Admin portals
    path('management/', views.user_management_view, name='user_management'),
    path('roles/', views.role_management_view, name='role_management'),
    path('analytics/', views.analytics_dashboard_view, name='analytics_dashboard'),
    path('import-staff/', views.bulk_staff_import_view, name='bulk_staff_import'),
    path('import-staff/sample/', views.download_sample_roster_csv, name='download_sample_roster'),
    path('audit-log/', views.audit_log_view, name='audit_log'),

    # Universal Procurement & Voucher Routing Pipeline
    path('procurement/', views.procurement_dashboard_view, name='procurement_dashboard'),
    path('procurement/create/', views.create_procurement_memo_view, name='create_procurement_memo'),
    path('procurement/<int:pk>/', views.procurement_detail_view, name='procurement_detail'),
    path('procurement/<int:pk>/advance/', views.advance_procurement_memo_view, name='advance_procurement_memo'),
]