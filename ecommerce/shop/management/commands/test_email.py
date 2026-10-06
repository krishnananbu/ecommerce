from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('django.mail')

class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email address to send the test message to')

    def handle(self, *args, **options):
        recipient = options['email']
        
        try:
            self.stdout.write(f"Attempting to send test email to {recipient}...")
            
            # Log email settings
            self.stdout.write("Email settings:")
            self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"Host: {settings.EMAIL_HOST}")
            self.stdout.write(f"Port: {settings.EMAIL_PORT}")
            self.stdout.write(f"TLS: {settings.EMAIL_USE_TLS}")
            self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
            
            # Send test email
            send_mail(
                subject='Test Email from Swiftbuy',
                message='This is a test email to verify the email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False
            )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully sent test email to {recipient}'))
            
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}'))