from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_no', 'address']
    search_fields = ['name', 'email', 'phone_no']

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubcategoryInline]

    # Method to count the number of subcategories
    def get_subcategory_count(self, obj):
        return obj.subcategory_set.count()

    get_subcategory_count.short_description = 'Subcategory Count'

    # Display the 'category_name' and the count of associated subcategories
    list_display = ['category_name', 'get_subcategory_count']
    search_fields = ['category_name']
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'email', 'contact_number']
    search_fields = ['customer_name', 'email', 'contact_number']
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['display_image', 'name', 'seller', 'subcategory', 'price', 'quantity_in_stock']
    list_filter = ['seller', 'subcategory']
    search_fields = ['name']

    def display_image(self, obj):
        return format_html('<img src="{}" width="50px" height="50px" />', obj.image_1.url)

    display_image.short_description = 'Image'

    def changelist_view(self, request, extra_context=None):
        # Check stock levels for each product
        for product in Product.objects.all():
            if product.quantity_in_stock < product.reorder_level:
                messages.warning(request, f"Low stock alert: {product.name}")

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit
            return self.readonly_fields + ('quantity_in_stock',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if change:  # obj is being edited
            original = Product.objects.get(pk=obj.pk)
            obj.quantity_in_stock = original.quantity_in_stock  # Preserve original quantity_in_stock
        super().save_model(request, obj, form, change)

# admin.site.register(Product, ProductAdmin)
    
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price', 'canceled']
    can_delete = False
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['id', 'customer__customer_name', 'customer__email']
    readonly_fields = ['customer', 'address', 'order_date', 'payment_method', 'total_amount']
    inlines = [OrderItemInline]
    
    def order_id(self, obj):
        return f"#{obj.id}"
    order_id.short_description = 'Order ID'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
        
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            old_status = Order.objects.get(pk=obj.pk).status
            new_status = obj.status
            
            # Log the status change
            messages.info(request, f'Order #{obj.id} status changed from {old_status} to {new_status}')
            
            # Send email notification to customer
            subject = f'Order #{obj.id} Status Update'
            message = f'Your order #{obj.id} status has been updated from {old_status} to {new_status}.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [obj.customer.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                messages.error(request, f'Failed to send email notification: {str(e)}')
    
class InventoryProduct(Product):
    class Meta:
        proxy = True
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventory'

class InventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity_in_stock', 'reorder_level', 'sku']
    list_filter = ['seller','subcategory']
    fields = ('quantity_in_stock', 'reorder_level', 'sku')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in obj._meta.fields if f.name not in ['quantity_in_stock', 'reorder_level', 'sku']]
    
    def changelist_view(self, request, extra_context=None):
        # Check stock levels for each product
        for product in InventoryProduct.objects.all():
            if product.quantity_in_stock < product.reorder_level:
                messages.warning(request, f"Low stock alert: {product.name}")
                
                # Send email to admin
                send_mail(
                    'Low stock alert',
                    f'The product "{product.name}" is low on stock.',
                    settings.EMAIL_HOST_USER,  # Replace with your email
                    ['jantheres01@gmail.com.com'],  # Replace with admin email
                    fail_silently=False,
                )

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)
    
admin.site.register(InventoryProduct, InventoryAdmin)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ['Quantity', 'Product', 'PurchaseUnitPrice', 'TotalAmount']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class PurchaseOrderAdmin(admin.ModelAdmin):
    def purchase_order_display(self, obj):
        return f"{obj.id} -{obj.PurchaseOrderDate}"
    purchase_order_display.short_description = 'Purchase Order'

    list_display = ['purchase_order_display', 'TotalAmount', 'PurchaseOrderDate', 'Status', 'ExpectedDeliveryDate', 'Seller']
    inlines = [PurchaseOrderItemInline]
    readonly_fields = [f.name for f in PurchaseOrder._meta.fields]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(Status='Not Initiated')

    def has_add_permission(self, request):
        return False


admin.site.register(PurchaseOrder, PurchaseOrderAdmin)


@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ('product', 'total_amount', 'quantity', 'confirmed',)
    list_filter = ('confirmed',)
    search_fields = ('product_name', 'purchase_order_id')
    
    def has_add_permission(self, request):
        return False


    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return [f.name for f in self.model._meta.fields if f.name not in ['quantity', 'confirmed']]
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(confirmed=False)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'description']
    search_fields = ['name']

@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'user', 'phone_number', 'expertise', 'is_available', 'rating']
    list_filter = ['expertise', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'phone_number']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

@admin.register(ServiceAppointment)
class ServiceAppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_customer_name', 'get_customer_contact', 'service', 'appointment_date', 'appointment_time', 'status', 'payment_status', 'get_technician_name']
    list_filter = ['status', 'payment_status', 'appointment_date', 'service']
    search_fields = ['customer__customer_name', 'customer__email', 'customer__contact_number', 'service__name', 'technician__user__first_name']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'
    
    def get_customer_name(self, obj):
        return f"{obj.customer.customer_name} ({obj.customer.email})"
    get_customer_name.short_description = 'Customer'
    get_customer_name.admin_order_field = 'customer__customer_name'
    
    def get_customer_contact(self, obj):
        return obj.customer.contact_number
    get_customer_contact.short_description = 'Contact'
    get_customer_contact.admin_order_field = 'customer__contact_number'
    
    def get_technician_name(self, obj):
        if obj.technician:
            return f"{obj.technician.user.get_full_name()}"
        return "Not Assigned"
    get_technician_name.short_description = 'Technician'
    get_technician_name.admin_order_field = 'technician__user__first_name'
    
    fieldsets = (
        ('Customer Information', {
            'fields': (
                'customer',
                ('appointment_date', 'appointment_time'),
                'address',
            )
        }),
        ('Service Details', {
            'fields': (
                'service',
                'technician',
                'special_instructions',
            )
        }),
        ('Status & Payment', {
            'fields': (
                'status',
                'payment_status',
                'total_amount',
            )
        }),
        ('Feedback & Notes', {
            'fields': (
                'completion_notes',
                'customer_rating',
                'customer_feedback',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New appointment
            obj.payment_amount = obj.service.price
        super().save_model(request, obj, form, change)
        
        # Send email notifications
        if change and 'status' in form.changed_data:
            subject = f'Service Appointment Status Update - {obj.status.title()}'
            html_message = render_to_string('services/email/status_update.html', {
                'appointment': obj,
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [obj.customer.email],
                html_message=html_message,
            )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'technician'):
            return qs.filter(technician=request.user.technician)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'technician'):
            return obj.technician == request.user.technician
        return False

@admin.register(TVExchange)
class TVExchangeAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'brand', 'model', 'status', 'exchange_value', 'created_at']
    list_filter = ['status', 'created_at', 'condition']
    search_fields = ['customer__customer_name', 'brand', 'model']
    readonly_fields = ['customer', 'product', 'brand', 'model', 'screen_size', 'age_in_years', 'condition', 'original_price', 'exchange_value', 'created_at']
    
    actions = ['approve_exchange', 'reject_exchange']
    
    def approve_exchange(self, request, queryset):
        for exchange in queryset:
            if exchange.status == 'pending':
                exchange.status = 'approved'
                exchange.save()  # This will trigger the automatic exchange value calculation
                
                # Send email notification to customer
                subject = 'TV Exchange Request Approved'
                html_message = render_to_string('emails/exchange_approved.html', {
                    'exchange': exchange,
                })
                plain_message = strip_tags(html_message)
                
                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [exchange.customer.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.error(request, f"Email notification failed: {str(e)}")
                
        messages.success(request, f"{queryset.count()} exchange request(s) approved successfully.")
    approve_exchange.short_description = "Approve selected exchange requests"
    
    def reject_exchange(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        messages.success(request, f"{queryset.count()} exchange request(s) rejected.")
    reject_exchange.short_description = "Reject selected exchange requests"
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer', 'created_at')
        }),
        ('Old TV Details', {
            'fields': ('brand', 'model', 'screen_size', 'age_in_years', 'condition', 'original_price')
        }),
        ('New TV Details', {
            'fields': ('product',)
        }),
        ('Exchange Status', {
            'fields': ('status', 'exchange_value', 'admin_notes')
        })
    )

    def has_add_permission(self, request):
        return False  # Prevent adding exchanges through admin