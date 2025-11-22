from rest_framework import serializers
from .models import Reservation, PaymentProof
from django.contrib.auth import get_user_model

User = get_user_model()

class ReservationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='ticket_type.event.title', read_only=True)
    event_location = serializers.CharField(source='ticket_type.event.location', read_only=True)
    event_start_datetime = serializers.DateTimeField(source='ticket_type.event.start_datetime', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    reservation_fee = serializers.DecimalField(source='ticket_type.reservation_fee', max_digits=10, decimal_places=2, read_only=True)
    
    guest_email = serializers.EmailField(required=False)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('reference_code', 'reserved_at', 'expires_at', 'status', 'user', 'total_amount', 'amount_paid', 'outstanding_balance') 
    
    def validate(self, data):
        user = self.context['request'].user
        
        if user and user.is_authenticated:
            data['guest_email'] = user.email
        else:
            if not data.get('guest_email'):
                raise serializers.ValidationError({'guest_email': "Email is required for guest reservations."})

        ticket_type = data.get('ticket_type')
        quantity = data.get('quantity', 1)
        
        if ticket_type and quantity > ticket_type.quantity_available:
            raise serializers.ValidationError('Not enough tickets available')
        
        return data

class PaymentProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProof
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'uploaded_at', 'verification_status')
    
    def create(self, validated_data):
        if self.context['request'].user.is_authenticated:
            validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)