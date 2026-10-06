from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Admin portals
    path('management/', views.user_management_view, name='user_management'),
    path('roles/', views.role_management_view, name='role_management'),
]