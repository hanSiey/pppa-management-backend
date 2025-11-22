from django.contrib.auth.models import AbstractUser, BaseUserManager # Import BaseUserManager
from django.db import models

# --- New Custom Manager ---
class CustomUserManager(BaseUserManager):

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        
        # Ensure username field is set to email before save
        user.username = email 
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin') # Set default admin role
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('attendee', 'Attendee'),
        ('organizer', 'Organizer'),
        ('finance', 'Finance'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendee')
    is_verified = models.BooleanField(default=False)
    
    # Do not set username = None. It's needed for AbstractUser's internal logic.
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    # Apply the custom manager
    objects = CustomUserManager() 

    def __str__(self):
        return f"{self.full_name} ({self.email})"