from django.db import models

class AnalyticsEvent(models.Model):
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('reservation_attempt', 'Reservation Attempt'),
        ('payment_upload', 'Payment Upload'),
        ('user_registration', 'User Registration'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.SET_NULL, null=True, blank=True)
    payload = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"

class NotificationLog(models.Model):
    NOTIFICATION_TYPES = [
        ('reservation_confirmation', 'Reservation Confirmation'),
        ('payment_reminder', 'Payment Reminder'),
        ('payment_received', 'Payment Received'),
        ('event_reminder', 'Event Reminder'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    # Allow null user for guest notifications
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    recipient_email = models.EmailField(blank=True, null=True) # Added to track guest emails
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    
    def __str__(self):
        email = self.recipient_email or (self.user.email if self.user else 'Unknown')
        return f"{self.type} to {email} - {self.sent_at}"