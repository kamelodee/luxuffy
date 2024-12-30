from datetime import timezone
from django.contrib import admin
from .models import Vendor

class VendorAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'store_name', 'verification_status','account_status','meta_title','meta_description','meta_keywords','canonical_url', 'verification_date', 'created_at')
    list_filter = ('verification_status', 'country')
    search_fields = ('business_name', 'store_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'verification_date')
    fields = (
        'user', 'business_name', 'business_type', 'store_name', 
        'logo', 'banner', 
        'phone_number', 'address_line1', 'address_line2', 
        'city', 'state', 'country', 'postal_code', 
        'verification_status', 'verification_date', 'verification_notes',
        'account_status','meta_title','meta_description','meta_keywords','canonical_url',
        'created_at', 'updated_at'
    )

    def save_model(self, request, obj, form, change):
        """Automatically set verification date when the status changes to verified."""
        if obj.verification_status == 'verified' and not obj.verification_date:
            obj.verification_date = timezone.now()
        super().save_model(request, obj, form, change)

admin.site.register(Vendor, VendorAdmin)
