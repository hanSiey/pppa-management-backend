from rest_framework import serializers
from .models import Payment, Refund, BankingDetail

class PaymentSerializer(serializers.ModelSerializer):
    reservation_reference = serializers.CharField(source='reservation.reference_code', read_only=True)
    event_title = serializers.CharField(source='reservation.ticket_type.event.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'paid_at')

class RefundSerializer(serializers.ModelSerializer):
    payment_details = PaymentSerializer(source='payment', read_only=True)
    requester_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = ('requested_at', 'processed_at')

class BankingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingDetail
        fields = '__all__'