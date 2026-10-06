from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Test email templates by sending a test email'

    def handle(self, *args, **kwargs):
        # Create a test context
        context = {
            'user': {
                'first_name': 'Test',
                'email': 'test@example.com'
            },
            'site_url': settings.SITE_URL
        }

        # Render the email template
        html_message = render_to_string('shop/email/welcome.html', context)
        
        # Send the test email
        try:
            send_mail(
                subject='Test: Welcome to Swiftbuy',
                message='',  # Plain text version (empty as we're using HTML)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
                html_message=html_message
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully sent test email to %s' % settings.EMAIL_HOST_USER)
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Failed to send email: %s' % str(e))
            )