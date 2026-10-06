from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('compose/', views.compose_memo, name='compose_memo'),
]