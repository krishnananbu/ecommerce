from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from shop.models import Order

class OrderInline(admin.TabularInline):
    model = Order
    fk_name = 'user'
    extra = 0
    readonly_fields = ['id', 'tracking_number', 'total_amount', 'status', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class CustomUserAdmin(BaseUserAdmin):
    inlines = (OrderInline,)
    list_display = BaseUserAdmin.list_display + ('is_active',)
    list_filter = BaseUserAdmin.list_filter + ('groups',)
    
    # Add block/unblock action
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Mark selected users as active/unblocked"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Mark selected users as inactive/blocked"

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
