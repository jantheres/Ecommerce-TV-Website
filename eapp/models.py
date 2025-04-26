import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Address(models.Model):
    recepient_name = models.CharField(max_length=100, null=True)
    recepient_contact = models.CharField(max_length=12, null=True, validators=[MinLengthValidator(10)])
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.address_line1}, {self.address_line2}, {self.city}, {self.state} - {self.postal_code}"    

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=12, blank=True, null=True, validators=[MinLengthValidator(10)])
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, default='customer')

    def __str__ (self):
        return self.customer_name
   
    

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=12, unique=True, validators=[MinLengthValidator(10)])
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.category_name

class Subcategory(models.Model):
    subcategory_name = models.CharField(max_length=100)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.subcategory_name

class Product(models.Model):
    seller = models.ForeignKey('Seller', on_delete=models.CASCADE)
    subcategory = models.ForeignKey('Subcategory', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=0)
    cost = models.DecimalField(max_digits=7, decimal_places=0, default=100)
    image_1 = models.ImageField(upload_to='product_images/')  # Mandatory field
    image_2 = models.ImageField(upload_to='product_images/', blank=True, null=True)  # Optional
    image_3 = models.ImageField(upload_to='product_images/', blank=True, null=True)  # Optional
    image_4 = models.ImageField(upload_to='product_images/', blank=True, null=True)  # Optional
    quantity_in_stock = models.PositiveIntegerField(default=0)
    sku = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Check if the quantity has gone below the reorder level
        if self.quantity_in_stock < self.reorder_level:
            # Create a new PurchaseOrder
            purchase_order = PurchaseOrder.objects.create(
                TotalAmount=self.cost * self.sku,
                PurchaseOrderDate=datetime.date.today(),
                Status='Not Initiated',
                Seller=self.seller,
            )

            # Create a new PurchaseOrderItem
            PurchaseOrderItem.objects.create(
                Quantity=self.sku,
                Product=self,
                PurchaseOrder=purchase_order,
                PurchaseUnitPrice=self.cost,
            )

            # Send a message to the admin
            AdminMessage.objects.create(
                product=self,
                quantity=self.sku,
                purchase_order=purchase_order,
            )

        super().save(*args, **kwargs)




class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def sub_total(self):
        return int(self.product.price) * int(self.quantity)

    def __str__(self):
        return f"Cart - Customer: {self.customer.customer_name} - Product: {self.product.name} - Qty: {self.quantity}"
    
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Shipped/Dispatched', 'Shipped/Dispatched'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
        ('Returned', 'Returned'),
        ('On Hold', 'On Hold'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=10, default='cod')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.customer_name}"

    def total_price(self):
        total = sum(item.total_price() for item in self.orderitem_set.filter(canceled=False))
        return total
        
    @property
    def is_cancelled(self):
        return any(item.canceled for item in self.orderitem_set.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    canceled = models.BooleanField(default=False)
    
    def total_price(self):
        if self.canceled:
            return 0
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"


# Define the PurchaseOrder model
class PurchaseOrder(models.Model):
    TotalAmount = models.DecimalField(max_digits=20, decimal_places=2)
    PurchaseOrderDate = models.DateField()
    Status = models.CharField(max_length=250, blank=True)
    ExpectedDeliveryDate = models.DateField(blank=True, null=True)
    Seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    seller_message = models.TextField(blank=True)
    def __str__(self):
        return f"Purchase Order {self.id}"

class PurchaseOrderItem(models.Model):
    Quantity = models.IntegerField()
    Product = models.ForeignKey(Product, on_delete=models.CASCADE)
    PurchaseOrder = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    PurchaseUnitPrice = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TotalAmount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate total amount before saving
        if self.Quantity is not None and self.PurchaseUnitPrice is not None:
            self.TotalAmount = self.Quantity * self.PurchaseUnitPrice
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Purchase Order Item {self.id}"
    


class AdminMessage(models.Model):
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Admin Message for {self.product.name} - Quantity: {self.quantity} - Purchase Order: {self.purchase_order.id}"

    def save(self, *args, **kwargs):
        # Calculate the total amount when the message is saved
        self.total_amount = self.quantity * self.product.cost
        super().save(*args, **kwargs)

    
    
@receiver(post_save, sender=AdminMessage)
def update_purchase_order_status(sender, instance, **kwargs):
    # If the admin confirms the message, update the status of the PurchaseOrder
    if instance.confirmed:
        instance.purchase_order.Status = 'Initiated'
        instance.purchase_order.TotalAmount = instance.quantity * instance.product.cost
        instance.purchase_order.save()

        # Update the quantity in the PurchaseOrderItem
        purchase_order_item = PurchaseOrderItem.objects.get(PurchaseOrder=instance.purchase_order, Product=instance.product)
        purchase_order_item.Quantity = instance.quantity
        purchase_order_item.TotalAmount = instance.quantity * instance.product.cost
        purchase_order_item.save()


class Technician(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=12, validators=[MinLengthValidator(10)])
    expertise = models.CharField(max_length=100, choices=[
        ('installation', 'TV Installation'),
        ('repair', 'TV Repair'),
        ('maintenance', 'TV Service/Maintenance'),
    ])
    is_available = models.BooleanField(default=True)
    is_on_leave = models.BooleanField(default=False)
    leave_start_date = models.DateField(null=True, blank=True)
    leave_end_date = models.DateField(null=True, blank=True)
    leave_reason = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_on_leave:
            self.is_available = False
        super().save(*args, **kwargs)

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.technician.name}'s leave request ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        # If leave is approved, update technician's leave status
        if self.status == 'approved':
            self.technician.is_on_leave = True
            self.technician.leave_start_date = self.start_date
            self.technician.leave_end_date = self.end_date
            self.technician.leave_reason = self.reason
            self.technician.save()
        elif self.status == 'rejected' and self.technician.leave_start_date == self.start_date:
            # If this specific leave request is rejected, clear the technician's leave status
            self.technician.is_on_leave = False
            self.technician.leave_start_date = None
            self.technician.leave_end_date = None
            self.technician.leave_reason = None
            self.technician.save()
        super().save(*args, **kwargs)

class Service(models.Model):
    SERVICE_TYPES = [
        ('installation', 'TV Installation'),
        ('repair', 'TV Repair'),
        ('maintenance', 'TV Service/Maintenance'),
    ]
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField(help_text="Estimated service duration")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_service_type_display()} - {self.name}"

class ServiceAppointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Technician Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('completed', 'Payment Completed'),
        ('refunded', 'Payment Refunded'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    base_service_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    technician_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completion_notes = models.TextField(blank=True, null=True)
    customer_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    customer_feedback = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"Appointment for {self.customer} - {self.service} on {self.appointment_date}"

    def save(self, *args, **kwargs):
        if not self.base_service_amount and self.service:
            self.base_service_amount = self.service.price
        self.total_amount = self.base_service_amount + self.technician_fee
        super().save(*args, **kwargs)

class TVExchange(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='exchanges')
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    age_in_years = models.IntegerField()
    condition = models.CharField(max_length=50, choices=[
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ])
    screen_size = models.CharField(max_length=20)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    images = models.ImageField(upload_to='tv_exchange_images/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending_review', 'Pending Review'),
        ('approved', 'Exchange Approved'),
        ('rejected', 'Exchange Rejected'),
        ('pending_pickup', 'Pending Pickup'),
        ('picked_up', 'Picked Up'),
        ('quality_check', 'Quality Check In Progress'),
        ('quality_passed', 'Quality Check Passed'),
        ('quality_failed', 'Quality Check Failed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending_review')
    quality_check_notes = models.TextField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(null=True, blank=True)

    def calculate_exchange_value(self):
        try:
            # Ensure original_price is a proper numeric value
            base_value = float(self.original_price)
            
            # Ensure age_in_years is treated as an integer
            try:
                age = int(self.age_in_years)
            except (ValueError, TypeError):
                age = 0  # Default to zero if conversion fails
                
            # Depreciation based on age
            age_factor = max(0.1, 1 - (age * 0.15))  # 15% depreciation per year, minimum 10% value
            
            # Condition multiplier
            condition_multipliers = {
                'excellent': 0.8,
                'good': 0.6,
                'fair': 0.4,
                'poor': 0.2
            }
            condition_factor = condition_multipliers.get(self.condition, 0.2)
            
            # Ensure all values are properly converted to numeric types before multiplication
            self.exchange_value = round(float(base_value) * float(age_factor) * float(condition_factor), 2)
            return self.exchange_value
        except Exception as e:
            # Fallback to prevent crashing
            print(f"Error calculating exchange value: {e}")
            self.exchange_value = 0
            return 0

    def save(self, *args, **kwargs):
        if not self.exchange_value:
            self.calculate_exchange_value()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Exchange Request #{self.id} - {self.brand} {self.model}"

class ExchangePickup(models.Model):
    exchange = models.OneToOneField(TVExchange, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    pickup_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=[
        ('morning', 'Morning (9 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 3 PM)'),
        ('evening', 'Evening (3 PM - 6 PM)'),
    ], default='morning')
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('technician_assigned', 'Technician Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled')
    ], default='scheduled')
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    pickup_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pickup #{self.id} for Exchange #{self.exchange.id}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            # Generate a unique tracking number
            import uuid
            self.tracking_number = f"PK{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class ExchangeOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('pickup_scheduled', 'Pickup Scheduled'),
        ('item_collected', 'Item Collected'),
        ('quality_check', 'Quality Check'),
        ('exchange_approved', 'Exchange Approved'),
        ('exchange_rejected', 'Exchange Rejected'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    exchange_request = models.OneToOneField(TVExchange, on_delete=models.CASCADE)
    new_order = models.OneToOneField(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    exchange_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    quality_check_date = models.DateTimeField(null=True, blank=True)
    quality_check_result = models.BooleanField(null=True, blank=True)
    quality_check_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(null=True, blank=True)

    def calculate_final_amount(self):
        if self.new_order and self.exchange_value:
            self.final_amount = max(0, self.new_order.total_amount - self.exchange_value)
        return self.final_amount

    def __str__(self):
        return f"Exchange Order #{self.id} for Customer {self.customer.customer_name}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            # Generate a unique tracking number
            import uuid
            self.tracking_number = f"EX{uuid.uuid4().hex[:8].upper()}"
        
        if not self.final_amount:
            self.calculate_final_amount()
            
        super().save(*args, **kwargs)
