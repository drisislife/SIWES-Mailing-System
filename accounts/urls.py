from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Admin portals
    path('management/', views.user_management_view, name='user_management'),
    path('roles/', views.role_management_view, name='role_management'),

    # Universal Procurement & Voucher Routing Pipeline
    path('procurement/', views.procurement_dashboard_view, name='procurement_dashboard'),
    path('procurement/create/', views.create_procurement_memo_view, name='create_procurement_memo'),
    path('procurement/<int:pk>/', views.procurement_detail_view, name='procurement_detail'),
    path('procurement/<int:pk>/advance/', views.advance_procurement_memo_view, name='advance_procurement_memo'),
]