from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    
    # This is the critical line Django needs to find your compose_memo button!
    path('messaging/', include('messaging.urls')), 
]