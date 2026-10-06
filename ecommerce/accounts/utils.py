import base64
import os
from django.conf import settings
from django.contrib.auth.models import User
from .signals import send_welcome_email as _signal_send_welcome_email

def send_welcome_email(request, user):
    """Helper to send welcome email manually if needed"""
    return _signal_send_welcome_email(sender=User, instance=user, created=True)

def get_logo_base64():
    """Convert the logo image to base64 string for email embedding"""
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png')
    if not os.path.exists(logo_path) and hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        logo_path = os.path.join(settings.STATIC_ROOT, 'logo', 'logo.png')
    try:
        with open(logo_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading logo file: {e}")
        return None