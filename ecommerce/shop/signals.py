from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.staticfiles import finders
from email.mime.image import MIMEImage
from xhtml2pdf import pisa
import os
import io
from django.contrib.auth.models import User
from .models import Order, OrderItem, OrderStatus, Product


@receiver(post_delete, sender=OrderItem)
def restore_product_stock(sender, instance, **kwargs):
    """
    Restore product stock when an order item is deleted
    """
    product = instance.product
    product.stock += instance.quantity
    product.save()

@receiver(pre_save, sender=Product)
def check_low_stock(sender, instance, **kwargs):
    """
    Check if product stock is low and send notification
    """
    try:
        old_instance = Product.objects.get(pk=instance.pk)
        # Check if stock has been updated and is now below threshold
        if old_instance.stock != instance.stock and instance.stock <= instance.low_stock_threshold:
            # Send low stock notification
            subject = f'Low Stock Alert: {instance.name}'
            message = f'Product {instance.name} has low stock ({instance.stock} remaining). Threshold is {instance.low_stock_threshold}.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )
    except Product.DoesNotExist:
        pass  # New product being created

import logging

logger = logging.getLogger('shop.signals')

@receiver(post_save, sender=Order)
def order_status_notification(sender, instance, created, **kwargs):
    """
    Send notifications when order is created or status changes
    """
    # Only send email if order has a tracking number
    if not instance.tracking_number:
        logger.info(f"Order #{instance.id} saved without tracking number. Skipping email.")
        return
    
    # Check if this is a status change (not creation)
    status_changed = not created and instance.status != instance.tracker.previous('status')
    
    # Send email for new orders or status changes
    if created or status_changed:
        logger.info(f"Triggering notification for Order #{instance.id}. Created: {created}, Status changed: {status_changed}")
        context = {
            'order': instance,
            'status': instance.get_status_display(),
            'tracking_number': instance.tracking_number,
            'is_new_order': created,
            'items': instance.items.select_related('product').all(),
            'subtotal': instance.subtotal,
            'contact_email': settings.DEFAULT_FROM_EMAIL,
            'now': timezone.now()
        }
        
        # Build tracking URL
        try:
            from django.urls import reverse
            # Note: Hardcoding domain for emails as request is not always available in signals
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            tracking_url = f"{site_url}{reverse('shop:track_order')}?order_number={instance.tracking_number}"
            context['tracking_url'] = tracking_url
        except:
            context['tracking_url'] = '#'
        
        # Choose appropriate template based on whether it's a new order or status update
        if created:
            # For new orders, this would be handled by send_order_confirmation_email in utils
            # So we skip sending duplicate email here
            logger.info(f"Order #{instance.id} is new. Confirmation email should be handled by views/utils.")
            return
        else:
            # Send status update email
            logger.info(f"Sending status update email for Order #{instance.id} to {instance.email}. New status: {instance.status}")
            
            # Use specific template based on status
            template_name = 'shop/email/order_status_update.html'
            if instance.status == 'shipped':
                template_name = 'shop/email/order_shipped_email.html'
            elif instance.status == 'delivered':
                template_name = 'shop/email/order_delivered_email.html'
            
            try:
                html_message = render_to_string(template_name, context)
                plain_message = strip_tags(html_message)
                
                subject = f'Order #{instance.id} Status Update'
                if instance.status == 'delivered':
                    subject = f'Your Order #{instance.id} has been Delivered! - Swiftbuy'
                
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = instance.email
                
                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    from_email,
                    [to_email]
                )
                msg.attach_alternative(html_message, "text/html")
                
                # Attach logo image
                logo_path = finders.find('logo/logo.png')
                if logo_path:
                    with open(logo_path, 'rb') as f:
                        logo_data = f.read()
                        image = MIMEImage(logo_data)
                        image.add_header('Content-ID', '<logo>')
                        msg.attach(image)
                
                # If delivered, generate and attach Invoice PDF
                if instance.status == 'delivered':
                    try:
                        # Render the PDF template
                        pdf_html = render_to_string('shop/email/invoice_pdf.html', context)
                        pdf_out = io.BytesIO()
                        pisa_status = pisa.CreatePDF(io.BytesIO(pdf_html.encode("utf-8")), dest=pdf_out)
                        
                        if not pisa_status.err:
                            msg.attach(f'Invoice_{instance.tracking_number}.pdf', pdf_out.getvalue(), 'application/pdf')
                            logger.info(f"Invoice PDF attached for Order #{instance.id}")
                        else:
                            logger.error(f"PDF generation error for Order #{instance.id}: {pisa_status.err}")
                    except Exception as pdf_err:
                        logger.error(f"Failed to generate/attach PDF for Order #{instance.id}: {str(pdf_err)}")
                
                msg.send(fail_silently=False)
                logger.info(f"Status update email sent successfully for Order #{instance.id}")
            except Exception as e:
                logger.error(f"Failed to send status update email for Order #{instance.id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

@receiver(post_save, sender=OrderStatus)
def create_order_status_history(sender, instance, created, **kwargs):
    """
    Update order status when a new status update is created
    """
    if created:
        order = instance.order
        order.status = instance.status
        if instance.status == 'delivered':
            order.delivered_date = timezone.now()
        elif instance.status == 'shipped':
            order.shipped_date = timezone.now()
        order.save()

@receiver(pre_save, sender=Product)
def handle_product_availability(sender, instance, **kwargs):
    """
    Automatically update product availability based on stock
    """
    if instance.stock <= 0:
        instance.available = False
    elif instance.stock > 0 and not instance.available:
        # Only set to True if it was previously False and now has stock
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            if old_instance.stock <= 0:
                instance.available = True
        except Product.DoesNotExist:
            # New product being created with stock
            instance.available = True