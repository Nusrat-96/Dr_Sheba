from django.contrib import admin
from django.contrib.admin import AdminSite


class DrShebaAdminSite(AdminSite):
    """Custom admin site with Dr. Sheba branding."""
    site_header = "Dr. Sheba Admin"
    site_title = "Dr. Sheba Admin"
    index_title = "Dashboard"

    # Template customization
    login_template = "admin/login.html"
    index_template = "admin/index.html"
    app_index_template = "admin/index.html"
    change_list_template = "admin/change_list.html"
    change_form_template = "admin/change_form.html"
    delete_confirmation_template = "admin/delete_confirmation.html"


# Create the custom admin site instance
drsheba_admin_site = DrShebaAdminSite(name='admin')

# Replace the default admin site with our custom one
admin.site = drsheba_admin_site
