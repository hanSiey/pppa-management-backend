import os
import django

# Ensure this matches your project name 'config'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = 'admin@email.com'
password = '12345@admin'
# full_name is a required field in your User model
full_name = 'System Administrator' 

# Check by email since USERNAME_FIELD = 'email'
if not User.objects.filter(email=email).exists():
    # Your CustomUserManager.create_superuser takes (email, password, **extra_fields)
    User.objects.create_superuser(
        email=email, 
        password=password, 
        full_name=full_name
    )
    print(f"Superuser {email} created.")
else:
    print(f"Superuser {email} already exists.")