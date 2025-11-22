from rest_framework import serializers
from .models import AnalyticsEvent, NotificationLog

class AnalyticsEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AnalyticsEvent
        fields = '__all__'
        read_only_fields = ('timestamp',)

class NotificationLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    reservation_reference = serializers.CharField(source='reservation.reference_code', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ('sent_at',)