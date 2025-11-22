from rest_framework import serializers
from .models import Event, SubEvent, TicketType

class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = '__all__'

class SubEventSerializer(serializers.ModelSerializer):
    ticket_types = TicketTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = SubEvent
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    sub_events = SubEventSerializer(many=True, read_only=True)
    ticket_types = TicketTypeSerializer(many=True, read_only=True)
    available_tickets = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('created_by', 'slug')
    
    def get_available_tickets(self, obj):
        return obj.capacity  # This would calculate actual availability

class EventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'title', 'slug', 'location', 'start_datetime', 'end_datetime', 'published')