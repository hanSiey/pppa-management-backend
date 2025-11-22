import uuid
from icalendar import Calendar, Event as IcalEvent
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.utils import timezone
# Import NotificationLog to enable logging
from analytics.models import NotificationLog

class CalendarService:
    @staticmethod
    def generate_ics_file(reservation):
        cal = Calendar()
        cal.add('prodid', '-//Parliament of Plating//Calendar//EN')
        cal.add('version', '2.0')
        
        event = IcalEvent()
        event.add('summary', reservation.ticket_type.event.title)
        event.add('description', f'Reservation: {reservation.reference_code}')
        event.add('dtstart', reservation.ticket_type.event.start_datetime)
        event.add('dtend', reservation.ticket_type.event.end_datetime)
        event.add('location', reservation.ticket_type.event.address)
        event.add('uid', f'{reservation.reference_code}@parliamentplating.com')
        
        cal.add_component(event)
        
        return cal.to_ical()
    
    @staticmethod
    def get_google_calendar_link(reservation):
        base_url = "https://calendar.google.com/calendar/render"
        params = {
            'action': 'TEMPLATE',
            'text': reservation.ticket_type.event.title,
            'dates': f"{reservation.ticket_type.event.start_datetime.strftime('%Y%m%dT%H%M%SZ')}/"
                    f"{reservation.ticket_type.event.end_datetime.strftime('%Y%m%dT%H%M%SZ')}",
            'details': f'Reservation: {reservation.reference_code}',
            'location': reservation.ticket_type.event.address,
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    @staticmethod
    def get_outlook_calendar_link(reservation):
        base_url = "https://outlook.live.com/calendar/0/deeplink/compose"
        params = {
            'subject': reservation.ticket_type.event.title,
            'startdt': reservation.ticket_type.event.start_datetime.isoformat(),
            'enddt': reservation.ticket_type.event.end_datetime.isoformat(),
            'body': f'Reservation: {reservation.reference_code}',
            'location': reservation.ticket_type.event.address,
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

class EmailService:
    @staticmethod
    def _log_notification(reservation, type_code, subject, content):
        try:
            NotificationLog.objects.create(
                user=reservation.user, # Can be None now
                recipient_email=reservation.guest_email,
                reservation=reservation,
                type=type_code,
                channel='email',
                subject=subject,
                content=content,
                status='sent'
            )
        except Exception as e:
            print(f"Error logging notification: {e}")

    @staticmethod
    def send_reservation_confirmation(reservation):
        subject = f"Reservation Confirmed - {reservation.ticket_type.event.title}"
        content = f"Dear Guest,\n\nYour reservation ({reservation.reference_code}) has been confirmed."
        print(f"Sending email to {reservation.guest_email}: {subject}")
        
        EmailService._log_notification(
            reservation, 'reservation_confirmation', subject, content
        )
        
    @staticmethod
    def send_payment_reminder(reservation):
        subject = f"Payment Reminder - {reservation.ticket_type.event.title}"
        content = "Please complete your payment to secure your spot."
        print(f"Sending email to {reservation.guest_email}: {subject}")
        
        EmailService._log_notification(
            reservation, 'payment_reminder', subject, content
        )
        
    @staticmethod
    def send_payment_confirmation(reservation):
        subject = f"Payment Received - {reservation.ticket_type.event.title}"
        content = f"We have received your payment of R {reservation.amount_paid}."
        print(f"Sending email to {reservation.guest_email}: {subject}")
        
        EmailService._log_notification(
            reservation, 'payment_received', subject, content
        )