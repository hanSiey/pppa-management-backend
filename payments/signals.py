from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import Payment

@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def update_reservation_payment_status(sender, instance, **kwargs):
    reservation = instance.reservation
    
    # Calculate total paid amount from all COMPLETED payments
    total_paid = reservation.payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    reservation.amount_paid = total_paid
    
    # Determine Status
    # 1. If fully paid
    if reservation.amount_paid >= reservation.total_amount:
        reservation.status = 'completed'
    
    # 2. If partially paid (at least deposit coverage)
    elif reservation.amount_paid > 0:
        # Check if it meets reservation fee requirement
        deposit_req = reservation.ticket_type.reservation_fee * reservation.quantity
        if reservation.amount_paid >= deposit_req:
            reservation.status = 'confirmed'
        else:
            # Paid something but less than deposit? Still technically confirmed as a spot holder?
            # Or keep as 'reserved' but with money paid? 
            # Let's stick to confirmed for any significant payment to secure spot
            reservation.status = 'confirmed'
            
    # 3. If nothing paid (and not cancelled)
    elif reservation.status not in ['cancelled', 'attended']:
        reservation.status = 'reserved'

    reservation.save()