from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import AnalyticsEvent, NotificationLog
from .serializers import AnalyticsEventSerializer, NotificationLogSerializer

from reservations.models import Reservation, PaymentProof 
from payments.models import Payment, Refund
from users.models import User
from events.models import Event

class AnalyticsEventViewSet(viewsets.ModelViewSet):
    serializer_class = AnalyticsEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return AnalyticsEvent.objects.all()
        return AnalyticsEvent.objects.filter(user=self.request.user)
    
    queryset = AnalyticsEvent.objects.all()
    
    @action(detail=False, methods=['post'])
    def track_event(self, request):
        event_type = request.data.get('event_type')
        payload = request.data.get('payload', {})
        
        if not event_type:
            return Response({'error': 'event_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        event = AnalyticsEvent.objects.create(
            event_type=event_type,
            user=request.user if request.user.is_authenticated else None,
            payload=payload,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_total_stats(self, request):
        # 1. Total Revenue (Lifetime)
        total_revenue = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0

        # 2. Pending Approvals Count
        pending_approvals = PaymentProof.objects.filter(verification_status='pending').count()
        
        # 3. Upcoming Events (List)
        upcoming_events_qs = Event.objects.filter(
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')
        
        upcoming_events_count = upcoming_events_qs.count()
        
        upcoming_events_list = list(upcoming_events_qs.values(
            'id', 'title', 'start_datetime', 'capacity', 'location', 'slug'
        )[:5])

        # 4. Total Users
        total_users = User.objects.count()
        
        # 5. Date Calculations
        today = timezone.now().date()
        # Extended lookback to ensure test data appears
        start_date = today - timedelta(days=365) 
        
        # 6. Revenue Trend
        # Group payments by date and sum amount
        revenue_trend = list(Payment.objects.filter(
            status='completed',
            paid_at__date__gte=start_date
        ).annotate(
            date=TruncDate('paid_at')
        ).values('date').annotate(
            total=Sum('amount')
        ).order_by('date'))

        # 7. Reservation Status Breakdown
        reservation_status_breakdown = list(Reservation.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        # 8. Pending Proofs List (Snippet)
        pending_proofs_data = list(PaymentProof.objects.filter(
            verification_status='pending'
        ).select_related('reservation').values(
            'id', 'uploaded_at', 'reservation__reference_code', 'reservation__total_amount', 'amount'
        )[:5]) 
        
        return {
            'total_events': Event.objects.count(),
            'total_reservations': Reservation.objects.count(),
            'total_revenue': total_revenue,
            'total_users': total_users,
            'pending_approvals_count': pending_approvals,
            'upcoming_events_count': upcoming_events_count,
            'upcoming_events_list': upcoming_events_list,
            'revenue_trend': revenue_trend, 
            'reservation_status_breakdown': reservation_status_breakdown,
            'pending_proofs_list': pending_proofs_data,
        }

    @action(detail=False, methods=['get'])
    def unified_dashboard_stats(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        stats = self.get_total_stats(request)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        return self.unified_dashboard_stats(request)

class NotificationLogViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return NotificationLog.objects.all().order_by('-sent_at')
        return NotificationLog.objects.filter(user=self.request.user).order_by('-sent_at')
    
    @action(detail=False, methods=['get'])
    def notification_stats(self, request):
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        stats = {
            'total_sent': NotificationLog.objects.count(),
            'sent_today': NotificationLog.objects.filter(sent_at__date=today).count(),
            'sent_this_week': NotificationLog.objects.filter(sent_at__date__gte=week_ago).count(),
            'by_type': NotificationLog.objects.values('type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'by_channel': NotificationLog.objects.values('channel').annotate(
                count=Count('id')
            ).order_by('-count'),
        }
        return Response(stats)