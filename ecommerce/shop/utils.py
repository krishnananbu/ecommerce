import logging
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.staticfiles import finders
from smtplib import SMTPException
import traceback
from email.mime.image import MIMEImage

logger = logging.getLogger('django.mail')

def send_order_confirmation_email(request, order):
    """
    Send order confirmation email with tracking number
    """
    try:
        logger.info(f"Preparing to send order confirmation email for order #{order.id}")
        
        # Build the tracking URL with the order's tracking number
        base_tracking_url = request.build_absolute_uri(reverse('shop:track_order'))
        tracking_url = f"{base_tracking_url}?order_number={order.tracking_number}"
        logger.debug(f"Generated tracking URL: {tracking_url}")
        
        # Get the site URL for static files
        site_url = f"{request.scheme}://{request.get_host()}"
        
        # Prepare the context with full order details
        context = {
            'order': order,
            'tracking_url': tracking_url,
            'site_name': 'Swiftbuy',
            'contact_email': settings.DEFAULT_FROM_EMAIL,
            'subtotal': sum(item.get_total_price() for item in order.items.all()),
            'items': order.items.select_related('product').all(),  # Optimize query
            'site_url': site_url,  # Add site_url for static files
        }
        
        # Render email templates
        try:
            html_content = render_to_string('shop/email/order_confirmation_email.html', context)
            text_content = strip_tags(html_content)
            logger.debug("Email templates rendered successfully")
        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}\nContext: {context}")
            raise
        
        # Create email with proper subject prefix
        subject = f'{settings.EMAIL_SUBJECT_PREFIX}Order #{order.id} Confirmation'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = order.email
        
        logger.info(f"Sending order confirmation email to {to_email} for order #{order.id}")
        
        try:
            # Create and send the email message
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                from_email,
                [to_email],
                headers={
                    'X-Order-ID': str(order.id),
                    'X-Tracking-Number': order.tracking_number
                }
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Attach logo image
            logo_path = finders.find('logo/logo.png')
            if logo_path:
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    image = MIMEImage(logo_data)
                    image.add_header('Content-ID', '<logo>')
                    msg.attach(image)
            
            # Attempt to send email with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    msg.send(fail_silently=False)
                    logger.info(f"Email sent successfully to {to_email} for order #{order.id}")
                    return True
                except SMTPException as smtp_error:
                    if attempt == max_retries - 1:  # Last attempt
                        raise
                    logger.warning(f"SMTP error on attempt {attempt + 1}/{max_retries}: {str(smtp_error)}")
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
            
        except SMTPException as e:
            logger.error(f"SMTP error while sending email: {str(e)}")
            logger.error(f"SMTP Details - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while sending email: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")
        logger.error(traceback.format_exc())
        return False  # Return False instead of raising to prevent checkout process from failing