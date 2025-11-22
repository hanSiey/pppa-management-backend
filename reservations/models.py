import uuid
import secrets
from django.db import models
from django.utils import timezone

def generate_reservation_code():
    return secrets.token_hex(6).upper()

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('reserved', 'Reserved'),
        ('pending', 'Pending Verification'),
        ('confirmed', 'Confirmed'), # Deposit Paid / Secured
        ('completed', 'Completed'), # Fully Paid
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    guest_email = models.EmailField()
    ticket_type = models.ForeignKey('events.TicketType', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved')
    reference_code = models.CharField(max_length=12, default=generate_reservation_code, unique=True, editable=False)
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def outstanding_balance(self):
        return self.total_amount - self.amount_paid

    def __str__(self):
        return f"Reservation {self.reference_code} - {self.guest_email}"

class PaymentProof(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    reservation = models.ForeignKey(Reservation, related_name='payment_proofs', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='payment_proofs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    # New field to track declared payment amount
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment proof for {self.reservation.reference_code} (R {self.amount})"