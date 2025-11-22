from django.urls import path
from . import views

urlpatterns = [
    # Payment endpoints
    path('payments/', views.PaymentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='payment-list'),
    
    path('payments/<int:pk>/', views.PaymentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='payment-detail'),
    
    path('payments/<int:pk>/mark-completed/', views.PaymentViewSet.as_view({
        'post': 'mark_completed'
    }), name='payment-mark-completed'),
    
    path('payments/stats/', views.PaymentViewSet.as_view({
        'get': 'stats'
    }), name='payment-stats'),
    
    # Refund endpoints
    path('refunds/', views.RefundViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='refund-list'),
    
    path('refunds/<int:pk>/', views.RefundViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='refund-detail'),
    
    path('refunds/<int:pk>/approve/', views.RefundViewSet.as_view({
        'post': 'approve'
    }), name='refund-approve'),
    
    path('refunds/<int:pk>/process/', views.RefundViewSet.as_view({
        'post': 'process'
    }), name='refund-process'),
    
    path('refunds/<int:pk>/reject/', views.RefundViewSet.as_view({
        'post': 'reject'
    }), name='refund-reject'),

    # Banking Details endpoints
    path('banking-details/', views.BankingDetailViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='banking-detail-list'),

    path('banking-details/<int:pk>/', views.BankingDetailViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='banking-detail-detail'),
]