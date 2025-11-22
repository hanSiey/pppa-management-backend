from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid

from reservations.models import PaymentProof
from reservations.serializers import PaymentProofSerializer

from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Payment, Refund, BankingDetail
from .serializers import PaymentSerializer, RefundSerializer, BankingDetailSerializer

class PaymentProofViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentProofSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PaymentProof.objects.all()
        return PaymentProof.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload_for_reservation(self, request):
        reservation_id = request.data.get('reservation_id')
        file = request.FILES.get('file')
        
        if not file:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = settings.ALLOWED_FILE_TYPES
        if file.content_type not in allowed_types:
            return Response(
                {'error': f'File type not allowed. Allowed types: {", ".join(allowed_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size
        if file.size > settings.MAX_UPLOAD_SIZE:
            return Response(
                {'error': f'File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.name)[1]
            filename = f"payment_proofs/{uuid.uuid4()}{file_extension}"
            
            # Save file
            saved_path = default_storage.save(filename, ContentFile(file.read()))
            file_url = default_storage.url(saved_path)
            
            # Create payment proof record
            payment_proof = PaymentProof.objects.create(
                reservation_id=reservation_id,
                uploaded_by=request.user,
                file=saved_path
            )
            
            serializer = self.get_serializer(payment_proof)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        # Users can only see payments for their own reservations
        return Payment.objects.filter(reservation__user=self.request.user)
    
    queryset = Payment.objects.all()
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark payment as completed (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        payment = self.get_object()
        transaction_ref = request.data.get('transaction_reference')
        payment.mark_as_completed(transaction_ref)
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get payment statistics (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Today's stats
        today = timezone.now().date()
        today_payments = Payment.objects.filter(paid_at__date=today, status='completed')
        
        # This week stats
        week_ago = today - timedelta(days=7)
        week_payments = Payment.objects.filter(paid_at__date__gte=week_ago, status='completed')
        
        # This month stats
        month_ago = today - timedelta(days=30)
        month_payments = Payment.objects.filter(paid_at__date__gte=month_ago, status='completed')
        
        stats = {
            'today': {
                'count': today_payments.count(),
                'amount': today_payments.aggregate(total=Sum('amount'))['total'] or 0
            },
            'this_week': {
                'count': week_payments.count(),
                'amount': week_payments.aggregate(total=Sum('amount'))['total'] or 0
            },
            'this_month': {
                'count': month_payments.count(),
                'amount': month_payments.aggregate(total=Sum('amount'))['total'] or 0
            },
            'payment_methods': Payment.objects.filter(status='completed').values(
                'payment_method'
            ).annotate(
                count=Count('id'),
                total=Sum('amount')
            )
        }
        
        return Response(stats)

class RefundViewSet(viewsets.ModelViewSet):
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Refund.objects.all()
        # Users can only see their own refund requests
        return Refund.objects.filter(requested_by=self.request.user)
    
    queryset = Refund.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve refund request (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        refund.status = 'approved'
        refund.save()
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Mark refund as processed (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        refund.status = 'processed'
        refund.processed_at = timezone.now()
        refund.save()
        
        return Response({'status': 'processed'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject refund request (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        refund.status = 'rejected'
        refund.notes = request.data.get('notes', '')
        refund.save()
        
        return Response({'status': 'rejected'})

class BankingDetailViewSet(viewsets.ModelViewSet):
    queryset = BankingDetail.objects.all()
    serializer_class = BankingDetailSerializer
    
    def get_permissions(self):
        # Allow anyone to view banking details (needed for public reservation page)
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        # Only admin can modify
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BankingDetail.objects.all()
        # Public only sees active accounts
        return BankingDetail.objects.filter(is_active=True)