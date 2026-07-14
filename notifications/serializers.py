from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    bien = serializers.PrimaryKeyRelatedField(read_only=True)
    reservation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id', 'user', 'message', 'is_read', 'created_at',
            'type', 'bien', 'reservation', 'conversation_id',
        )
        read_only_fields = ('id', 'user', 'created_at')


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('message',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
