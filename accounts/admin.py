from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Address, Order, OrderItem, WishlistItem, Notification, NotificationSettings

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'is_staff', 'get_email_verified')
    list_filter = ('is_staff', 'is_superuser', 'profile__email_verified')
    
    def get_email_verified(self, obj):
        return obj.profile.email_verified
    get_email_verified.short_description = 'Email Verified'
    get_email_verified.admin_order_field = 'profile__email_verified'

    fieldsets = UserAdmin.fieldsets + (
        ('Verification', {'fields': ('profile__email_verified', 'profile__verification_token')}),
        ('Password Reset', {'fields': ('profile__password_reset_token', 'profile__password_reset_expires')}),
    )

# Unregister the default User admin
admin.site.unregister(User)
# Register User model with custom admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(WishlistItem)
admin.site.register(Notification)
admin.site.register(NotificationSettings)