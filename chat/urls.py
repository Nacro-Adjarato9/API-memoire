from django.urls import path

from .views import MessageConversationView

urlpatterns = [
    path('messages/conversation/<str:conversation_id>/', MessageConversationView.as_view(), name='messages_conversation'),
]
