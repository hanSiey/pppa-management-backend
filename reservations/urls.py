from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reservations', views.ReservationViewSet, basename='reservation')
router.register(r'payment-proofs', views.PaymentProofViewSet, basename='paymentproof')

urlpatterns = [
    path('', include(router.urls)),
    
    # Payment Proof endpoints
    path('payment-proofs/', views.PaymentProofViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='paymentproof-list'),
    
    path('payment-proofs/<int:pk>/', views.PaymentProofViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='paymentproof-detail'),
    
    path('payment-proofs/<int:pk>/approve/', views.PaymentProofViewSet.as_view({
        'post': 'approve'
    }), name='paymentproof-approve'),
    
    path('payment-proofs/<int:pk>/reject/', views.PaymentProofViewSet.as_view({
        'post': 'reject'
    }), name='paymentproof-reject'),
]