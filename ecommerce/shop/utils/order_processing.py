from decimal import Decimal
from django.utils.crypto import get_random_string
from datetime import date, timedelta
from django.db import transaction
from django.core.exceptions import ValidationError
from .logging import log_order_step, OrderError, order_logger
from ..models import Order, OrderItem, OrderStatus, Product

@log_order_step("validate_cart")
def validate_cart(cart, user_id=None):
    """Validate cart contents and product availability"""
    try:
        if not cart or len(cart) == 0:
            raise OrderError("Cart is empty", code="EMPTY_CART", user_id=user_id)
        
        if not isinstance(cart, dict) and not hasattr(cart, '__iter__'):
            raise OrderError("Invalid cart format", code="INVALID_CART", user_id=user_id)
        
        unavailable_products = []
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Lock the products for update with a timeout
                    product_ids = [item['product'].id for item in cart]
                    try:
                        # Use a timeout instead of nowait
                        products = Product.objects.select_for_update().filter(id__in=product_ids)
                        products_dict = {p.id: p for p in products}
                        break  # Success - exit retry loop
                    except transaction.TransactionManagementError as e:
                        if attempt == max_retries - 1:  # Last attempt
                            raise OrderError(
                                "The system is experiencing high load. Please try again in a moment.",
                                code="LOCK_ERROR",
                                user_id=user_id,
                                details={"attempt": attempt + 1, "max_retries": max_retries}
                            )
                        order_logger.warning(
                            f"Lock acquisition failed, attempt {attempt + 1}/{max_retries}",
                            extra={"user_id": user_id, "product_ids": product_ids}
                        )
                        import time
                        time.sleep(retry_delay)  # Wait before retrying
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise OrderError(
                        f"Error accessing product information: {str(e)}",
                        code="PRODUCT_ACCESS_ERROR",
                        user_id=user_id
                    )
                continue  # Try again
        
        for item in cart:
            product_id = item['product'].id
            product = products_dict.get(product_id)
            
            if not product:
                unavailable_products.append(f"{item['product'].name} is no longer available")
                continue
                
            if not product.available:
                unavailable_products.append(f"{product.name} is no longer available for purchase")
            elif product.stock < item['quantity']:
                unavailable_products.append(
                    f"{product.name} has insufficient stock (requested: {item['quantity']}, "
                    f"available: {product.stock})"
                )
        
        if unavailable_products:
            raise OrderError(
                "Product availability issues",
                code="PRODUCT_UNAVAILABLE",
                user_id=user_id,
                details=unavailable_products
            )
        
        return products_dict
    except Exception as e:
        # Log the error and re-raise
        if not isinstance(e, OrderError):
            e = OrderError(
                f"Error validating cart: {str(e)}",
                code="VALIDATION_ERROR",
                user_id=user_id
            )
        raise

@log_order_step("create_order")
def create_order(form, cart, user, products_dict):
    """Create the order with proper locking and validation"""
    # Validate form data
    if not hasattr(form, 'is_valid') or not form.is_valid():
        raise OrderError(
            "Invalid form data", 
            code="FORM_ERROR",
            user_id=user.id if user else None,
            details=getattr(form, 'errors', {'error': 'Invalid form data'})
        )
    
    # Validate user
    if not user or not user.is_authenticated:
        raise OrderError(
            "User authentication required",
            code="AUTH_ERROR"
        )
    
    order = form.save(commit=False)
    order.user = user
    order.status = 'pending'
    order.payment_status = 'pending'
    
    # Set estimated delivery
    today = date.today()
    if order.shipping_method == 'express':
        order.estimated_delivery = today + timedelta(days=3)
    elif order.shipping_method == 'standard':
        order.estimated_delivery = today + timedelta(days=7)
    elif order.shipping_method == 'pickup':
        order.estimated_delivery = today + timedelta(days=1)

    # Calculate totals
    subtotal = Decimal(str(cart.get_total_price()))
    shipping_cost = Decimal('0.00')
    
    if order.shipping_method == 'standard':
        shipping_cost = Decimal('5.00')
    elif order.shipping_method == 'express':
        shipping_cost = Decimal('15.00')
    
    tax = (subtotal + shipping_cost) * Decimal('0.10')
    
    order.subtotal = subtotal
    order.shipping_cost = shipping_cost
    order.tax = tax
    order.total_amount = subtotal + shipping_cost + tax

    # Generate tracking number
    order.tracking_number = get_random_string(10).upper()
    order.save()
    
    # Record initial pending status
    OrderStatus.objects.create(
        order=order,
        status='pending',
        note='Order placed successfully',
        created_by=order.user
    )
    
    return order

@log_order_step("create_order_items")
def create_order_items(order, cart, products_dict):
    """Create order items and update stock levels"""
    try:
        order_items = []
        stock_updates = []
        
        for item in cart:
            try:
                # Validate cart item structure
                if not isinstance(item, dict) or 'product' not in item:
                    raise OrderError(
                        "Invalid cart item format",
                        code="INVALID_CART_ITEM",
                        order_id=order.id
                    )
                
                product_id = item['product'].id
                if product_id not in products_dict:
                    raise OrderError(
                        f"Product {product_id} not found",
                        code="PRODUCT_NOT_FOUND",
                        order_id=order.id
                    )
                
                product = products_dict[product_id]
                
                # Validate quantity and price
                quantity = int(item.get('quantity', 0))
                if quantity <= 0:
                    raise OrderError(
                        f"Invalid quantity for {product.name}",
                        code="INVALID_QUANTITY",
                        order_id=order.id
                    )
                
                price = Decimal(str(item.get('price', '0')))
                if price <= 0:
                    raise OrderError(
                        f"Invalid price for {product.name}",
                        code="INVALID_PRICE",
                        order_id=order.id
                    )
                
                # Create OrderItem
                order_item = OrderItem(
                    order=order,
                    product=product,
                    price=price,
                    quantity=quantity
                )
                order_items.append(order_item)
                
                # Prepare stock update
                if product.stock < quantity:
                    raise OrderError(
                        f"Insufficient stock for {product.name}",
                        code="INSUFFICIENT_STOCK",
                        order_id=order.id
                    )
                
                product.stock -= quantity
                if product.stock == 0:
                    product.available = False
                stock_updates.append(product)
                
            except (TypeError, ValueError, KeyError) as e:
                raise OrderError(
                    f"Error processing cart item: {str(e)}",
                    code="CART_ITEM_ERROR",
                    order_id=order.id
                )
        
        # Bulk create order items and update stock in a transaction
        with transaction.atomic():
            OrderItem.objects.bulk_create(order_items)
            for product in stock_updates:
                product.save()
                
        return order_items
        
    except Exception as e:
        if not isinstance(e, OrderError):
            raise OrderError(
                f"Error creating order items: {str(e)}",
                code="ORDER_ITEMS_ERROR",
                order_id=order.id
            )
        raise

@log_order_step("process_payment")
def process_payment(order):
    """Handle dummy order validation and processing"""
    try:
        with transaction.atomic():
            # Basic validation checks
            if order.total_amount <= 0:
                raise OrderError(
                    "Invalid order amount",
                    code="VALIDATION_ERROR",
                    order_id=order.id,
                    user_id=order.user.id
                )
            
            # Validate shipping information
            if not all([order.address, order.city, order.state, order.zip_code]):
                raise OrderError(
                    "Incomplete shipping information",
                    code="VALIDATION_ERROR",
                    order_id=order.id,
                    user_id=order.user.id
                )
            
            # Validate phone number
            if not order.phone or len(order.phone) < 10:
                raise OrderError(
                    "Invalid phone number",
                    code="VALIDATION_ERROR",
                    order_id=order.id,
                    user_id=order.user.id
                )

            # Set appropriate status based on payment method
            if order.payment_method == 'cash_on_delivery':
                new_status = 'confirmed'
                payment_status = 'pending'
                status_note = 'Order confirmed - Cash on Delivery'
            else:
                # Simulate successful order placement
                new_status = 'processing'
                payment_status = 'completed'
                status_note = 'Order validated and confirmed'

            # Update order status
            order.status = new_status
            order.payment_status = payment_status
            order.save()

            # Create status update record
            OrderStatus.objects.create(
                order=order,
                status=new_status,
                note=status_note,
                created_by=order.user
            )
            
            order_logger.info(
                f"Order {order.id} validated and processed successfully",
                extra={
                    'order_id': order.id,
                    'user_id': order.user.id,
                    'status': new_status,
                    'payment_method': order.payment_method
                }
            )
            
            return True

    except OrderError:
        # Re-raise existing OrderErrors
        raise
    except Exception as e:
        error_message = f"Order validation failed: {str(e)}"
        order_logger.error(error_message, extra={
            'order_id': order.id,
            'user_id': order.user.id,
            'error_type': type(e).__name__
        })
        raise OrderError(
            error_message,
            code="VALIDATION_ERROR",
            order_id=order.id,
            user_id=order.user.id
        )