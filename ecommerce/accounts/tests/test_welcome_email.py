from django.test import SimpleTestCase
from django.core import mail
from django.template.loader import render_to_string
from django.conf import settings

class WelcomeEmailTests(SimpleTestCase):
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.context = {
            'user': self.user_data,
            'site_name': settings.STORE_NAME,
            'site_url': settings.SITE_URL
        }
        
        # Clear the test outbox
        mail.outbox = []

    def test_welcome_email_template_exists(self):
        """Test that the welcome email template can be rendered"""
        rendered = render_to_string('shop/email/welcome.html', self.context)
        self.assertTrue(rendered)

    def test_welcome_email_content(self):
        """Test the content of the welcome email"""
        html_content = render_to_string('shop/email/welcome.html', self.context)
        
        # Required elements
        required_elements = [
            settings.STORE_NAME,  # Store name should be in the email
            self.user_data['first_name'],  # User's name should be included
            'Welcome',  # Welcome message
            settings.SITE_URL,  # Site URL for the logo
            'logo',  # Logo reference
            'Start Your Shopping Journey'  # Call to action button
        ]
        
        for element in required_elements:
            self.assertIn(element, html_content, 
                         f"Required element '{element}' not found in welcome email")

    def test_welcome_email_logo_url(self):
        """Test that the logo URL is correctly formatted"""
        html_content = render_to_string('shop/email/welcome.html', self.context)
        expected_logo_url = f"{settings.SITE_URL}/static/logo/logo.png"
        self.assertIn(expected_logo_url, html_content)

    def test_welcome_email_with_missing_name(self):
        """Test welcome email with a user that has no first name"""
        user_without_name = {
            'username': 'noname',
            'email': 'noname@example.com'
        }
        context = {
            'user': user_without_name,
            'site_name': settings.STORE_NAME,
            'site_url': settings.SITE_URL
        }
        
        html_content = render_to_string('shop/email/welcome.html', context)
        self.assertIn(user_without_name['username'], html_content)

    def test_welcome_email_special_chars(self):
        """Test email rendering with special characters"""
        user_special_chars = {
            'username': 'special',
            'email': 'special@example.com',
            'first_name': 'Tést',
            'last_name': 'Üser'
        }
        context = {
            'user': user_special_chars,
            'site_name': settings.STORE_NAME,
            'site_url': settings.SITE_URL
        }
        
        html_content = render_to_string('shop/email/welcome.html', context)
        self.assertIn('Tést', html_content)  # Should find first name
        self.assertIn('special@example.com', html_content)  # Should find email

    def test_welcome_email_footer(self):
        """Test the email footer content"""
        html_content = render_to_string('shop/email/welcome.html', self.context)
        
        footer_elements = [
            'rights reserved',
            str(settings.STORE_NAME),
            self.user_data['email']
        ]
        
        for element in footer_elements:
            self.assertIn(element, html_content,
                         f"Footer element '{element}' not found in welcome email")