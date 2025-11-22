from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from decimal import Decimal

from .models import Reservation, PaymentProof
from .serializers import ReservationSerializer, PaymentProofSerializer
from .services import CalendarService, EmailService
from payments.models import Payment

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        reference_code = self.request.query_params.get('reference_code')
        if reference_code:
            return Reservation.objects.filter(reference_code=reference_code)

        if not self.request.user.is_authenticated:
            return Reservation.objects.none()
            
        if self.request.user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            user = None
            
        ticket_type = serializer.validated_data['ticket_type']
        quantity = serializer.validated_data['quantity']
        
        total_amount = ticket_type.price * quantity
        amount_paid = Decimal('0.00') # Initialize with 0
        expires_at = timezone.now() + timezone.timedelta(hours=24)
        
        reservation = serializer.save(
            user=user,
            total_amount=total_amount,
            amount_paid=amount_paid,
            expires_at=expires_at
        )
    
    @action(detail=True, methods=['get'])
    def calendar_links(self, request, pk=None):
        reservation = self.get_object()
        links = {
            'google': CalendarService.get_google_calendar_link(reservation),
            'outlook': CalendarService.get_outlook_calendar_link(reservation),
            'ics_download': f'/api/reservations/{reservation.id}/download-ics/'
        }
        return Response(links)
    
    @action(detail=True, methods=['get'])
    def download_ics(self, request, pk=None):
        reservation = self.get_object()
        ics_content = CalendarService.generate_ics_file(reservation)
        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="reservation-{reservation.reference_code}.ics"'
        return response
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def upload_payment_proof(self, request, pk=None):
        reservation = self.get_object()
        file = request.FILES.get('file')
        amount = request.data.get('amount')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        if not amount:
            return Response({'error': 'Payment amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_by = request.user if request.user.is_authenticated else None

        payment_proof = PaymentProof.objects.create(
            reservation=reservation,
            uploaded_by=uploaded_by,
            file=file,
            amount=amount
        )
        
        reservation.status = 'pending'
        reservation.save()
        
        serializer = PaymentProofSerializer(payment_proof)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentProofViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentProofSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PaymentProof.objects.filter(verification_status='pending') # Admin mostly cares about pending
        return PaymentProof.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a payment proof (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        payment_proof = self.get_object()
        reservation = payment_proof.reservation
        
        # 1. Create actual Payment record
        # This ACTION triggers the 'post_save' signal in payments/signals.py
        # The signal automatically recalculates 'amount_paid' and updates 'status'
        Payment.objects.create(
            reservation=reservation,
            amount=payment_proof.amount,
            currency='ZAR',
            status='completed',
            payment_method='bank_transfer',
            paid_at=timezone.now(),
            transaction_reference=f"PROOF-{payment_proof.id}"
        )
        
        # 2. Update Verification Status
        payment_proof.verification_status = 'approved'
        payment_proof.save()
        
        # 3. Refresh Reservation from DB
        # We must refresh to get the calculations performed by the Signal
        reservation.refresh_from_db()
        
        # 4. Send confirmation emails using the FRESH state
        EmailService.send_payment_confirmation(reservation)
        if reservation.status in ['confirmed', 'completed']:
            EmailService.send_reservation_confirmation(reservation)
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        payment_proof = self.get_object()
        payment_proof.verification_status = 'rejected'
        payment_proof.notes = request.data.get('notes', '')
        payment_proof.save()
        
        # Revert reservation status to reserved if it was pending
        reservation = payment_proof.reservation
        if reservation.status == 'pending':
            reservation.status = 'reserved'
            reservation.save()
        
        return Response({'status': 'rejected'})