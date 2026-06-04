from django.db.models import Q
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Message
from .serializers import MessageSerializer, MessageCreateSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        conversation_id = self.request.query_params.get('conversation_id')
        sender = self.request.query_params.get('sender')
        receiver = self.request.query_params.get('receiver')

        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        if sender:
            queryset = queryset.filter(sender__username__iexact=sender)
        if receiver:
            queryset = queryset.filter(receiver__username__iexact=receiver)

        return queryset.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).distinct()

    @action(detail=False, methods=['get'])
    def mes_messages(self, request):
        """Récupérer les messages de l'utilisateur connecté"""
        messages = self.get_queryset().filter(
            sender=request.user
        ) | self.get_queryset().filter(
            receiver=request.user
        )
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Récupérer les conversations de l'utilisateur connecté"""
        # Récupérer tous les conversation_id où l'utilisateur est sender ou receiver
        sent_messages = Message.objects.filter(sender=request.user).values_list('conversation_id', flat=True).distinct()
        received_messages = Message.objects.filter(receiver=request.user).values_list('conversation_id', flat=True).distinct()
        
        conversation_ids = set(sent_messages) | set(received_messages)
        
        conversations = []
        for conv_id in conversation_ids:
            last_message = Message.objects.filter(conversation_id=conv_id).order_by('-created_at').first()
            if last_message:
                conversations.append({
                    'conversation_id': conv_id,
                    'last_message': MessageSerializer(last_message).data,
                    'unread_count': Message.objects.filter(
                        conversation_id=conv_id,
                        receiver=request.user,
                        is_read=False
                    ).count()
                })
        
        return Response(conversations)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Marquer un message comme lu"""
        message = self.get_object()
        if message.receiver == request.user:
            message.is_read = True
            message.save()
            return Response({'status': 'Message marqué comme lu'})
        return Response({'error': 'Non autorisé'}, status=403)


class MessageConversationView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(conversation_id=conversation_id).order_by('created_at')

