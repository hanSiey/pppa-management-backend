from django.urls import path
from . import views

urlpatterns = [
    # Analytics events endpoints
    path('analytics/events/', views.AnalyticsEventViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='analytics-event-list'),
    
    path('analytics/events/<int:pk>/', views.AnalyticsEventViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='analytics-event-detail'),
    
    path('analytics/events/track-event/', views.AnalyticsEventViewSet.as_view({
        'post': 'track_event'
    }), name='analytics-track-event'),
    
    path('analytics/events/dashboard-stats/', views.AnalyticsEventViewSet.as_view({
        'get': 'dashboard_stats'
    }), name='analytics-dashboard-stats'),
    
    path('dashboard/', views.AnalyticsEventViewSet.as_view({
        'get': 'unified_dashboard_stats'
    }), name='unified-dashboard-stats'),
    
    # Notification logs endpoints
    path('analytics/notifications/', views.NotificationLogViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='notification-log-list'),
    
    path('analytics/notifications/<int:pk>/', views.NotificationLogViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='notification-log-detail'),
    
    path('analytics/notifications/notification-stats/', views.NotificationLogViewSet.as_view({
        'get': 'notification_stats'
    }), name='notification-stats'),
]