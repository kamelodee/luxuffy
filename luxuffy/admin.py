from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    site_header = "Lexete admin"  # Change the header text
    site_title = "Lexete Admin Portal"  # Change the title text
    index_title = "Welcome to Lexete Admin Portal"  # Change the index title

admin_site = CustomAdminSite(name='custom_admin')
# Registering the Brand model to the Django admin