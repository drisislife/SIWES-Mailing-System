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
    path('<int:pk>/recall/',            views.memo_recall_view,          name='memo_recall'),
    path('<int:pk>/pdf/',               views.memo_pdf_view,             name='memo_pdf'),
    path('archive/',                    views.records_archive_view,      name='records_archive'),
    path('notices/',                    views.notice_board_view,         name='notice_board'),
    path('notifications/',              views.notifications_list_view,   name='notifications_list'),
    path('notifications/<int:pk>/read/',views.mark_notification_read_view,name='mark_notification_read'),
    path('notifications/read-all/',     views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('hod/approvals/',              views.hod_approvals_view,        name='hod_approvals'),
    path('hod/review/<int:pk>/',        views.hod_review_view,           name='hod_review'),

    # Council Broadcast & Circulars
    path('circulars/',                  views.circulars_list_view,       name='circulars_list'),
    path('circulars/create/',           views.create_circular_view,      name='create_circular'),
]
