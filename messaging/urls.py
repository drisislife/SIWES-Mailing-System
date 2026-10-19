from django.urls import path
from . import views

urlpatterns = [
    path('inbox/',                      views.inbox_view,                name='inbox'),
    path('sent/',                       views.sent_view,                 name='sent'),
    path('sent/messages/',              views.sent_view,                 name='sent_messages'),
    path('compose/',                    views.compose_view,              name='compose'),
    path('compose/memo/',               views.compose_view,              name='compose_memo'),
    path('compose/message/',            views.compose_view,              name='compose_message'),
    path('<int:pk>/',                   views.message_detail_view,        name='message_detail'),
    path('<int:pk>/delete/',            views.delete_message_view,       name='delete_message'),
    path('<int:pk>/toggle-read/',       views.toggle_message_read_view,  name='toggle_message_read'),
    path('hod/approvals/',              views.hod_approvals_view,        name='hod_approvals'),
    path('hod/review/<int:pk>/',        views.hod_review_view,           name='hod_review'),
]