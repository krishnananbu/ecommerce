from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from django.utils.crypto import get_random_string
from datetime import date, timedelta
from .models import Product, Category, Brand, Order, OrderItem, OrderStatus, Transaction
from .forms import ProductFilterForm, CartAddProductForm, CheckoutForm
from .cart import Cart
from .utils.logging import log_order_processing, OrderError, order_logger
from .utils.order_processing import (
    validate_cart,
    create_order,
    create_order_items,
    process_payment
)

def validate_order_status(status):
    valid_statuses = ['pending', 'processing', 'confirmed', 'cancelled', 'shipped', 'delivered', 'refunded']
    if status not in valid_statuses:
        raise ValidationError(f"Invalid status: {status}")
    return status

def product_list(request):
    products = Product.objects.select_related('category', 'brand').all()
    form = ProductFilterForm(request.GET)
    
    if form.is_valid():
        # Search filter
        search = form.cleaned_data.get('search')
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search) |
                Q(brand__name__icontains=search)
            )
        
        # Category filter
        category = form.cleaned_data.get('category')
        if category:
            products = products.filter(category=category)
        
        # Brand filter
        brand = form.cleaned_data.get('brand')
        if brand:
            products = products.filter(brand__in=brand)
        
        # Price range filter
        price_range = form.cleaned_data.get('price_range')
        price_max = form.cleaned_data.get('price_max')
        
        if price_max:
            products = products.filter(price__lte=price_max)
        elif price_range:
            if price_range == '0-50':
                products = products.filter(price__lt=50)
            elif price_range == '50-100':
                products = products.filter(price__gte=50, price__lt=100)
            elif price_range == '100-200':
                products = products.filter(price__gte=100, price__lt=200)
            elif price_range == '200-500':
                products = products.filter(price__gte=200, price__lt=500)
            elif price_range == '500+':
                products = products.filter(price__gte=500)
        
        # Featured filter
        featured_only = form.cleaned_data.get('featured_only')
        if featured_only:
            products = products.filter(featured=True)
        
        # Available filter
        available_only = form.cleaned_data.get('available_only')
        if available_only:
            products = products.filter(available=True, stock__gt=0)
        
        # Sort filter
        sort_by = form.cleaned_data.get('sort_by')
        if sort_by:
            products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'form': form,
        'total_products': products.count(),
    }
    
    return render(request, 'shop/product_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]
    
    cart_product_form = CartAddProductForm(max_quantity=product.stock)
    
    context = {
        'product': product,
        'related_products': related_products,
        'cart_product_form': cart_product_form,
    }
    
    return render(request, 'shop/product_detail.html', context)

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    brands = Brand.objects.all()

    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    price_range = request.GET.get('price_range')
    if price_range == '0-50':
        products = products.filter(price__lt=50)
    elif price_range == '50-100':
        products = products.filter(price__gte=50, price__lt=100)
    elif price_range == '100-200':
        products = products.filter(price__gte=100, price__lt=200)
    elif price_range == '200-500':
        products = products.filter(price__gte=200, price__lt=500)
    elif price_range == '500+':
        products = products.filter(price__gte=500)

    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by in ['name', '-name']:
        products = products.order_by(sort_by)

    if request.GET.get('featured_only'):
        products = products.filter(featured=True)

    if request.GET.get('available_only'):
        products = products.filter(available=True, stock__gt=0)
    else:
        products = products.filter(available=True)

    # Apply pagination
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
        'brands': brands,
    }

    return render(request, 'shop/category_products.html', context)

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                quantity=cd['quantity'],
                override_quantity=cd['override'])
    return redirect('shop:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            max_quantity=item['product'].stock,
            initial={
                'quantity': item['quantity'],
                'override': True
            }
        )
    return render(request, 'shop/cart/detail.html', {'cart': cart})

@login_required
@log_order_processing
def checkout(request):
    cart = Cart(request)
    
    # Check if cart is empty
    if len(cart) == 0:
        messages.error(request, "Your cart is empty!")
        return redirect('shop:product_list')
    
    # Lock prevention - store cart version in session
    cart_version = request.session.get('cart_version', 0)
        
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Verify cart hasn't changed
            if cart_version != request.session.get('cart_version', 0):
                messages.error(request, "Your cart has been modified. Please review your order and try again.")
                return redirect('shop:cart_detail')
            
            try:
                with transaction.atomic():
                    # Step 1: Validate cart and get locked products
                    products_dict = validate_cart(cart, user_id=request.user.id)
                    
                    # Step 2: Create the order (includes tracking number generation)
                    order = create_order(form, cart, request.user, products_dict)

                    # Step 3: Create order items and update stock
                    create_order_items(order, cart, products_dict)
                    
                    # Step 4: Process payment and update status
                    process_payment(order)

                    # Send confirmation email
                    try:
                        from .utils import send_order_confirmation_email
                        email_sent = send_order_confirmation_email(request, order)
                        if email_sent:
                            messages.success(
                                request,
                                f"Order #{order.id} placed successfully! "
                                f"Current Status: {order.get_status_display()}. "
                                f"A confirmation email has been sent to {order.email}"
                            )
                        else:
                            messages.warning(
                                request,
                                f"Order #{order.id} placed successfully. "
                                f"Please save your tracking number: {order.tracking_number}. "
                                "The confirmation email could not be sent."
                            )
                    except Exception:
                        messages.warning(
                            request,
                            f"Order #{order.id} placed successfully. "
                            f"Please save your tracking number: {order.tracking_number}. "
                            "The confirmation email could not be sent."
                        )

                    # Store order details and clear cart
                    request.session['recent_order_id'] = order.id
                    request.session['order_tracking_number'] = order.tracking_number
                    cart.clear()
                    
                    return redirect('shop:order_confirmation', order_id=order.id)

            except OrderError as e:
                # Handle specific order processing errors
                error_messages = {
                    'EMPTY_CART': "Your cart appears to be empty. Please add items and try again.",
                    'PRODUCT_UNAVAILABLE': "Some products in your cart are no longer available.",
                    'PAYMENT_ERROR': "There was an error processing your payment. Please try again.",
                    'STOCK_ERROR': "Some items in your cart are no longer in stock.",
                    'LOCK_ERROR': "The system is currently busy processing other orders. Please try again in a moment.",
                }
                
                error_msg = error_messages.get(e.code, str(e))
                messages.error(request, error_msg)
                
                # Log the error with additional context
                order_logger.error(
                    f"Order processing error: {error_msg}",
                    extra={
                        'error_code': e.code,
                        'user_id': request.user.id,
                        'cart_items': len(cart),
                        'error_details': e.details if hasattr(e, 'details') else None
                    }
                )
                
                if hasattr(e, 'details') and e.details:
                    for detail in e.details:
                        messages.error(request, detail)
                
                if e.code == 'LOCK_ERROR':
                    # For lock errors, stay on checkout page and show retry message
                    messages.info(request, "You can try again in a few seconds.")
                    return redirect('shop:checkout')
                else:
                    # For other errors, redirect based on the error type
                    return redirect('shop:cart_detail' if e.code in ['EMPTY_CART', 'PRODUCT_UNAVAILABLE', 'STOCK_ERROR'] else 'shop:checkout')
                
            except ValidationError as e:
                messages.error(request, f"Please check your information: {str(e)}")
                return redirect('shop:checkout')
                
            except transaction.TransactionManagementError:
                messages.error(
                    request,
                    "There was a problem processing your order due to a system issue. "
                    "Please try again in a few moments."
                )
                return redirect('shop:checkout')
                
            except Exception as e:
                # Log unexpected errors with full context
                order_logger.error(
                    f"Critical error during checkout for user {request.user.id}",
                    extra={
                        'user_id': request.user.id,
                        'error': str(e),
                        'cart_items': len(cart),
                        'total_amount': cart.get_total_price()
                    }
                )
                
                messages.error(
                    request,
                    "We encountered a technical issue while processing your order. "
                    "Our team has been notified and is working to resolve it. "
                    "Please try again in a few minutes or contact our support if the issue persists."
                )
    else:
        # Pre-fill form with user data if available
        initial_data = {}
        if request.user.first_name:
            initial_data['first_name'] = request.user.first_name
        if request.user.last_name:
            initial_data['last_name'] = request.user.last_name
        if request.user.email:
            initial_data['email'] = request.user.email
        form = CheckoutForm(initial=initial_data)
    
    return render(request, 'shop/checkout.html', {
        'cart': cart,
        'form': form
    })

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Validate order has items
    if not order.items.exists():
        messages.warning(request, "This order has no items.")
    
    # Validate order status
    try:
        validate_order_status(order.status)
    except ValidationError as e:
        messages.error(request, str(e))
        order.status = 'pending'  # Set to default status
        order.save()
    
    return render(request, 'shop/order_confirmation.html', {'order': order})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    status_updates = order.status_updates.all().order_by('-timestamp')
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'status_updates': status_updates
    })

def track_order(request):
    # Status weights for progress calculation
    status_weights = {
        'pending': 0,
        'processing': 25,
        'confirmed': 50,
        'shipped': 75,
        'out_for_delivery': 90,
        'delivered': 100,
        'cancelled': -1,
        'refunded': -1
    }

    # Get tracking number from either POST or GET
    tracking_number = request.POST.get('tracking_number') or request.GET.get('order_number')
    
    if tracking_number:
        tracking_number = tracking_number.strip()
        try:
            # Try to find order by tracking number or authenticated user ID
            try:
                order = Order.objects.get(tracking_number=tracking_number)
            except Order.DoesNotExist:
                if request.user.is_authenticated:
                    try:
                        if request.user.is_staff:
                            order = Order.objects.get(id=tracking_number)
                        else:
                            order = Order.objects.get(id=tracking_number, user=request.user)
                    except (Order.DoesNotExist, ValueError):
                        messages.error(request, 'Order not found. Please check your tracking number.')
                        return render(request, 'shop/track_order_form.html')
                else:
                    messages.error(request, 'Order not found. Please check your tracking number.')
                    return render(request, 'shop/track_order_form.html')

            # Calculate progress percentage
            progress_percentage = status_weights.get(order.status, 0)
            
            # If order is cancelled or refunded, show appropriate message
            if order.status in ['cancelled', 'refunded']:
                messages.warning(request, f'This order has been {order.status}.')
                progress_percentage = 0

            context = {
                'order': order,
                'progress_percentage': progress_percentage,
                'status_updates': order.status_updates.all().order_by('-timestamp'),
            }
            
            return render(request, 'shop/track_order.html', context)
            
        except Exception:
            messages.error(request, 'An error occurred while tracking your order. Please try again.')
            return render(request, 'shop/track_order_form.html')

    # If no tracking number provided, show the tracking form
    return render(request, 'shop/track_order_form.html')

@login_required
def order_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Only allow user who placed order or staff to view invoice
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('shop:product_list')
        
    return render(request, 'shop/invoice.html', {'order': order})

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta

@staff_member_required
def admin_dashboard(request, extra_context=None):
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    
    # Financial Stats - Include all orders that are not cancelled or failed
    valid_orders = Order.objects.exclude(status__in=['cancelled', 'payment_failed', 'refunded'])
    total_sales = valid_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    month_sales = valid_orders.filter(created_at__gte=month_ago).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(orders__isnull=False).distinct().count()
    
    # Best Sellers
    best_sellers = OrderItem.objects.values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('price') * F('quantity'))
    ).order_by('-total_sold')[:5]
    
    # Inventory Alerts
    inventory_alerts = Product.objects.filter(stock__lte=F('low_stock_threshold'))[:10]
    
    # Recent Transactions
    recent_transactions = Transaction.objects.order_by('-created_at')[:10]
    
    # Sales by Category
    sales_by_category = OrderItem.objects.values('product__category__name').annotate(
        total_rev=Sum(F('price') * F('quantity'))
    ).order_by('-total_rev')
    
    # Pre-process for template to avoid filter syntax errors
    for item in sales_by_category:
        item['total_rev_display'] = int(item['total_rev'] or 0)
    
    # Get standard admin app list
    from django.contrib import admin
    app_list = admin.site.get_app_list(request)
    
    # Pending Orders
    pending_orders_count = Order.objects.filter(status='pending').count()
    
    context = {
        'total_sales': total_sales,
        'month_sales': month_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'pending_orders_count': pending_orders_count,
        'best_sellers': best_sellers,
        'inventory_alerts': inventory_alerts,
        'recent_transactions': recent_transactions,
        'sales_by_category': sales_by_category,
        'app_list': app_list,
        'title': 'Analytics Dashboard',
        **(extra_context or {})
    }
    
    return render(request, 'shop/admin_dashboard.html', context)