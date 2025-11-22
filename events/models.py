from django.db import models
from django.utils.text import slugify

class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255)
    address = models.TextField()
    capacity = models.PositiveIntegerField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    currency = models.CharField(max_length=3, default='ZAR')
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class SubEvent(models.Model):
    event = models.ForeignKey(Event, related_name='sub_events', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.event.title} - {self.title}"

class TicketType(models.Model):
    event = models.ForeignKey(Event, related_name='ticket_types', on_delete=models.CASCADE)
    sub_event = models.ForeignKey(SubEvent, related_name='ticket_types', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reservation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_available = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"