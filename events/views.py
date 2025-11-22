from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Event, SubEvent, TicketType
from .serializers import EventSerializer, EventListSerializer, SubEventSerializer, TicketTypeSerializer
from users.permissions import IsAdminUserForCRUD

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.filter(published=True)
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['location', 'start_datetime']
    lookup_field = 'slug'
    permission_classes = [IsAdminUserForCRUD]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def get_queryset(self):
        queryset = Event.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(published=True)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(start_datetime__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_datetime__date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def calendar_events(self, request, slug=None):
        event = self.get_object()
        # Generate ICS file or calendar links
        return Response({'message': 'Calendar integration endpoint'})

class SubEventViewSet(viewsets.ModelViewSet):
    queryset = SubEvent.objects.all()
    serializer_class = SubEventSerializer
    permission_classes = [IsAdminUserForCRUD]

class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAdminUserForCRUD]
