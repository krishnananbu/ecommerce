from django.test import TestCase, Client, RequestFactory, override_settings
import tempfile
import shutil
from django.urls import reverse
from django.core import mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.staticfiles import finders
import os
from email.mime.image import MIMEImage

User = get_user_model()

@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test_db.sqlite3'
        }
    }
)
class EmailTests(TestCase):
    def setUp(self):
        """Set up test data and configurations"""
        self.client = Client()
        self.factory = RequestFactory()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
        
        # Clear the test outbox
        mail.outbox = []

    def test_welcome_email_template_exists(self):
        """Test that the welcome email template file exists"""
        template_path = 'shop/email/welcome.html'
        result = render_to_string(template_path, {'user': self.user})
        self.assertTrue(result, "Welcome template should render without errors")

    def test_welcome_email_logo_exists(self):
        """Test that the logo file exists in static files"""
        logo_path = finders.find('logo/logo.png')
        self.assertIsNotNone(logo_path, "Logo file not found in static files")
        self.assertTrue(os.path.exists(logo_path), 
                       "Logo file does not exist at the specified path")

    def test_welcome_email_content(self):
        """Test the content of the welcome email"""
        context = {
            'user': self.user,
            'site_name': settings.STORE_NAME,
            'login_url': f"{settings.SITE_URL}{reverse('accounts:login')}",
            'site_url': settings.SITE_URL
        }
        
        html_content = render_to_string('shop/email/welcome.html', context)
        
        # Check for required elements in the email
        required_elements = [
            settings.STORE_NAME,  # Store name
            self.user.first_name,  # User's name
            'Welcome',  # Welcome message
            'Start Your Shopping Journey',  # Call to action button
        ]
        
        for element in required_elements:
            self.assertIn(element, html_content, 
                         f"Required element '{element}' not found in welcome email")

    def test_welcome_email_sending(self):
        """Test sending the welcome email"""
        from accounts.utils import send_welcome_email
        
        request = self.factory.get('/')
        send_welcome_email(request, self.user)
        
        # Check that one message has been sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Get the sent email
        email = mail.outbox[0]
        
        # Check email properties
        self.assertEqual(email.to, [self.user.email])
        self.assertTrue('Welcome' in email.subject)
        self.assertTrue(email.alternatives, "No HTML alternative found")
        
        # Check for logo in email content
        html_content = email.alternatives[0][0]
        self.assertTrue('logo' in html_content.lower(), "Logo reference not found in email content")

    def test_welcome_email_with_missing_user_name(self):
        """Test welcome email with a user that has no first/last name"""
        user_without_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='testpass123'
        )
        
        context = {
            'user': user_without_name,
            'site_name': settings.STORE_NAME,
            'site_url': settings.SITE_URL
        }
        
        html_content = render_to_string('shop/email/welcome.html', context)
        
        # Should use username if no first name is available
        self.assertIn(user_without_name.username, html_content)

    def test_welcome_email_encoding(self):
        """Test email encoding and special characters handling"""
        user_special_chars = User.objects.create_user(
            username='special',
            email='special@example.com',
            password='testpass123',
            first_name='Tést',
            last_name='Üser'
        )
        
        context = {
            'user': user_special_chars,
            'site_name': settings.STORE_NAME,
            'site_url': settings.SITE_URL
        }
        
        html_content = render_to_string('shop/email/welcome.html', context)
        
        # Special characters should be preserved
        self.assertIn('Tést', html_content)

    def test_welcome_email_attachments(self):
        """Test that the welcome email properly attaches the logo"""
        from accounts.utils import send_welcome_email
        
        request = self.factory.get('/')
        send_welcome_email(request, self.user)
        
        email = mail.outbox[0]
        
        # Check for image/logo attachment
        has_image = False
        for attachment in getattr(email, 'attachments', []):
            if isinstance(attachment, MIMEImage) or (isinstance(attachment, tuple) and attachment[2] == 'image/png'):
                has_image = True
                break
                
        self.assertTrue(has_image, "Logo image should be attached to the email")