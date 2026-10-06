from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
from django.contrib.staticfiles import finders

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send welcome email to new users when they register
    """
    try:
        if created:  # Only send email when a new user is created
            print(f"Attempting to send welcome email to {instance.email}")
            
            # HTML Content
            html_message = render_to_string('accounts/email/welcome_email.html', {
                'user': instance
            })
            print("Email template rendered successfully")
            
            # Plain text content
            plain_message = strip_tags(html_message)
            
            # Send email
            print(f"Sending email to {instance.email}")
            
            # Create the email message
            email = EmailMultiAlternatives(
                subject='Welcome to Swiftbuy!',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.email]
            )
            
            # Attach HTML content
            email.attach_alternative(html_message, "text/html")
            
            # Attach logo image
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    email.attach('logo.png', f.read(), 'image/png')
            
            # Send the email
            email.send(fail_silently=False)
            print("Email sent successfully")
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        # Do not re-raise the exception so that user creation can still succeed 
        # even if email fails due to network or configuration issues.
