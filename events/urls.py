from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.EventViewSet)
router.register(r'sub-events', views.SubEventViewSet)
router.register(r'ticket-types', views.TicketTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]