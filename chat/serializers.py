from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')
    receiver = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = Message
        fields = ('id', 'conversation_id', 'sender', 'receiver', 'texte', 'created_at')
        read_only_fields = ('id', 'sender', 'created_at')


class MessageCreateSerializer(serializers.ModelSerializer):
    conversation_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Message
        fields = ('conversation_id', 'receiver', 'texte')

    def create(self, validated_data):
        sender = self.context['request'].user
        receiver = validated_data['receiver']
        if not validated_data.get('conversation_id'):
            validated_data['conversation_id'] = '-'.join(
                str(uid) for uid in sorted([sender.id, receiver.id])
            )
        validated_data['sender'] = sender
        return super().create(validated_data)
