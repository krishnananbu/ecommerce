from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from .models import (
    Category, Brand, Product, ProductImage, Order, OrderItem, 
    OrderStatus, Coupon, ShippingZone, ShippingCourier, 
    Transaction, Review, SupportTicket, SiteSettings, HomepageBanner
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['parent']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'brand', 'stock', 'available', 'featured']
    list_filter = ['available', 'featured', 'category', 'brand', 'created_at']
    list_editable = ['price', 'stock', 'available', 'featured']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    search_fields = ['name', 'description']
    
    # Low stock alert
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(is_low_stock=models.Case(
            models.When(stock__lte=models.F('low_stock_threshold'), then=True),
            default=False,
            output_field=models.BooleanField(),
        ))

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'active', 'usage_count']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_charge']

@admin.register(ShippingCourier)
class ShippingCourierAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'get_total_price']
    
    def get_total_price(self, instance):
        return instance.get_total_price() or 0.00
    get_total_price.short_description = 'Total'

class OrderStatusInline(admin.TabularInline):
    model = OrderStatus
    extra = 1
    fields = ['status', 'note', 'created_by', 'timestamp']
    readonly_fields = ['timestamp']

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ['transaction_id', 'amount', 'status', 'created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tracking_number', 'user', 'total_amount', 
        'status', 'payment_status', 'created_at', 'invoice_link'
    ]
    list_filter = ['status', 'payment_status', 'shipping_method', 'payment_method', 'created_at', 'courier_service']
    search_fields = ['id', 'tracking_number', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'tracking_number']
    inlines = [OrderItemInline, OrderStatusInline, TransactionInline]
    list_editable = ['status', 'payment_status']
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_refunded']

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    def mark_as_refunded(self, request, queryset):
        queryset.update(status='refunded', payment_status='refunded')

    def invoice_link(self, obj):
        url = reverse('shop:order_invoice', args=[obj.id])
        return format_html('<a href="{}" target="_blank">View Invoice</a>', url)
    invoice_link.short_description = 'Invoice'

    fieldsets = (
        ('Order Info', {
            'fields': ('tracking_number', 'user', 'status', 'payment_status', 'created_at', 'updated_at')
        }),
        ('Customer Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Logistics', {
            'fields': (
                'address', 'city', 'state', 'zip_code', 'shipping_method', 
                'delivery_partner', 'courier_service', 'estimated_delivery', 
                'shipped_date', 'delivered_date'
            )
        }),
        ('Payment & Finance', {
            'fields': ('payment_method', 'payment_date', 'coupon', 'subtotal', 'shipping_cost', 'tax', 'discount_amount', 'total_amount')
        }),
        ('Notes', {
            'fields': ('order_notes', 'admin_notes')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "delivery_partner":
            kwargs["queryset"] = User.objects.filter(groups__name='delivery')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'order__id']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['subject', 'message', 'user__username']

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

@admin.register(HomepageBanner)
class HomepageBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'active', 'order']
    list_editable = ['active', 'order']
