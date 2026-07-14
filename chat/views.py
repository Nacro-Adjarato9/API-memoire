from django.db.models import Q
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.services import notify

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
        message = serializer.save(sender=self.request.user)
        notify(
            message.receiver, f"Nouveau message de {self.request.user.username}",
            type='message', conversation_id=message.conversation_id,
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
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
            Q(sender=user) | Q(receiver=user)
        ).distinct()

    @action(detail=False, methods=['get'])
    def mes_messages(self, request):
        """Récupérer les messages de l'utilisateur connecté"""
        if not request.user.is_authenticated:
            return Response([])
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
        if not request.user.is_authenticated:
            return Response([])
        # Récupérer tous les conversation_id où l'utilisateur est sender ou receiver
        sent_messages = Message.objects.filter(sender=request.user).values_list('conversation_id', flat=True).distinct()
        received_messages = Message.objects.filter(receiver=request.user).values_list('conversation_id', flat=True).distinct()
        
        conversation_ids = set(sent_messages) | set(received_messages)
        
        conversations = []
        for conv_id in conversation_ids:
            last_message = Message.objects.filter(conversation_id=conv_id).order_by('-created_at').first()
            if last_message:
                # L'autre participant (celui qui n'est pas l'utilisateur connecte) : le
                # frontend en a besoin pour repondre, sinon il ne sait pas a qui envoyer.
                autre_participant = (
                    last_message.receiver if last_message.sender_id == request.user.id else last_message.sender
                )
                conversations.append({
                    'conversation_id': conv_id,
                    'receiver_id': autre_participant.id,
                    'receiver_username': autre_participant.username,
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
        if not request.user.is_authenticated:
            return Response({'status': 'Message marqué comme lu'})
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
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user),
            conversation_id=conversation_id,
        ).order_by('created_at')
