from datetime import date, datetime
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.views.generic import View
from django.forms import ModelForm
from .models import (
    Customer, ExchangeOrder, Seller, Category, Subcategory, Product, Cart, Order, OrderItem,
    PurchaseOrder, PurchaseOrderItem, AdminMessage, Technician, LeaveRequest,
    Service, ServiceAppointment, Address, TVExchange, ExchangePickup
)

# Form definitions
class AddressForm(ModelForm):
    class Meta:
        model = Address
        fields = ['recepient_name', 'recepient_contact', 'address_line1', 'address_line2', 'city', 'state', 'postal_code']

# Create your views here.
# Create your views here.
# def index(request):
#     products = Product.objects.all()
#     return render(request, 'index.html', {'products': products})

def index(request):
    # Fetch all products and categories
    products = Product.objects.all()
    categories = Category.objects.all()

    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Category filter functionality
    selected_category = request.GET.get('category', '')
    if selected_category:
        products = products.filter(subcategory__name=selected_category)

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    }
    return render(request, 'index.html', context)
    
def customer_dashboard(request):
    return render(request, 'customer/customer_dashboard.html')

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full-name')
        email = request.POST.get('your-email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        phone_number = request.POST.get('phone-number')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords Do Not Match!')
            return render(request, 'customer/register.html')

        # Check password strength using Django's built-in validators
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, ', '.join(e.messages))
            return render(request, 'customer/register.html')

        # Create user
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
        except:
            messages.error(request, 'Email already exists!')
            return render(request, 'customer/register.html')

        # Create customer
        customer = Customer.objects.create(user=user, customer_name=full_name, email=email, contact_number=phone_number)
        
        # Authenticate and login user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Your Account Has Been Registered Successfully!')
            return redirect('index')
        else:
            messages.error(request, 'Failed to login user.')
            return render(request, 'customer/register.html')

    return render(request, 'customer/register.html')




def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in!')
            
            # Redirect based on user role
            try:
                customer = user.customer
                return redirect('index')  # Redirect customer to index page
            except Customer.DoesNotExist:
                try:
                    seller = user.seller
                    return redirect('seller_purchase_orders')  # Redirect seller to seller dashboard
                except Seller.DoesNotExist:
                    messages.error(request, 'You are not authorized to access this page.')
                    return redirect('login')  # Redirect to login page if no associated role found

        else:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'customer/login.html')  # Change 'login.html' to your login template path
    return render(request, 'customer/login.html')  # Change 'login.html' to your login template path


def user_logout(request):
    logout(request)
    return redirect('index') 



@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user  # Assuming the user is already logged in

        if user.check_password(old_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password changed successfully.")
                return redirect('login')
            else:
                messages.error(request, "New passwords do not match.")
        else:
            messages.error(request, "Old password is incorrect.")

    return render(request, 'customer/change_password.html')


class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + user.password + str(timestamp)
        )



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = CustomTokenGenerator().make_token(user)
            reset_password_url = request.build_absolute_uri('/reset_password/{}/{}/'.format(uid, token))
            email_subject = 'Reset Your Password'

            # Render both HTML and plain text versions of the email
            email_body_html = render_to_string('customer/reset_password_email.html', {
                'reset_password_url': reset_password_url,
                'user': user,
            })
            email_body_text = "Click the following link to reset your password: {}".format(reset_password_url)

            # Create an EmailMultiAlternatives object to send both HTML and plain text versions
            email = EmailMultiAlternatives(
                email_subject,
                email_body_text,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email.attach_alternative(email_body_html, 'text/html')  # Attach HTML version
            email.send(fail_silently=False)

            messages.success(request, 'An email has been sent to your email address with instructions on how to reset your password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
    return render(request, 'customer/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and CustomTokenGenerator().check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully. You can now login with your new password.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, 'customer/reset_password.html')
    else:
        messages.error(request, "Invalid reset link. Please try again or request a new reset link.")
        return redirect('login')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Customer

@login_required
def edit_customer(request):
    # Retrieve the current logged-in user
    current_user = request.user
    # Check if the current user has a corresponding Customer instance
    try:
        customer = Customer.objects.get(user=current_user)
    except Customer.DoesNotExist:
        # Handle the case where the logged-in user does not have a corresponding Customer instance
        return HttpResponse("You are not associated with any customer profile.")

    if request.method == 'POST':
        # Update customer details with the data from the form
        customer.customer_name = request.POST['full-name']
        customer.email = request.POST['your-email']
        customer.contact_number = request.POST['phone-number']
        customer.save()

        # Update associated user's email
        current_user.email = request.POST['your-email']
        current_user.username = request.POST['your-email']
        current_user.save()

        # Redirect to the customer detail page after editing
        return redirect('index')

    # If it's a GET request, display the edit form with existing customer details
    return render(request, 'customer/edit_customer.html', {'customer': customer})


    

@login_required
def address_list(request):
    addresses = Address.objects.filter(customer=request.user.customer)
    return render(request, 'customer/address_list.html', {'addresses': addresses})

@login_required
def address_create(request):
    if request.method == 'POST':
        recepient_name = request.POST.get('recepient_name')
        recepient_contact = request.POST.get('recepient_contact')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        
        address = Address.objects.create(
            customer=request.user.customer,
            recepient_name=recepient_name,
            recepient_contact=recepient_contact,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code
        )
        
        messages.success(request, "Address added successfully!")
        return redirect('checkout')
        
    return render(request, 'address_form.html', {'form_type': 'Add'})

@login_required
def address_edit(request, address_id):
    try:
        address = Address.objects.get(id=address_id, customer=request.user.customer)
        
        if request.method == 'POST':
            address.recepient_name = request.POST.get('recepient_name')
            address.recepient_contact = request.POST.get('recepient_contact')
            address.address_line1 = request.POST.get('address_line1')
            address.address_line2 = request.POST.get('address_line2')
            address.city = request.POST.get('city')
            address.state = request.POST.get('state')
            address.postal_code = request.POST.get('postal_code')
            address.save()
            
            messages.success(request, "Address updated successfully!")
            return redirect('checkout')
            
        return render(request, 'address_form.html', {
            'address': address,
            'form_type': 'Edit'
        })
        
    except Address.DoesNotExist:
        messages.error(request, "Address not found.")
        return redirect('checkout')

@login_required
def address_delete(request, address_id):
    if request.method == 'POST':
        try:
            address = Address.objects.get(id=address_id, customer=request.user.customer)
            address.delete()
            messages.success(request, "Address deleted successfully!")
        except Address.DoesNotExist:
            messages.error(request, "Address not found.")
    return redirect('checkout')

@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = request.user.customer
            address.save()
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_edit(request, address_id):
    address = get_object_or_404(Address, pk=address_id, customer=request.user.customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_delete(request, address_id):
    address = get_object_or_404(Address, pk=address_id, customer=request.user.customer)
    if request.method == 'POST':
        address.delete()
        return redirect('address_list')
    return render(request, 'customer/address_confirm_delete.html', {'address': address})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)  # Fetch the product by ID
    return render(request, 'product_details.html', {'product': product})


@login_required
def cart(request):
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        # Create a customer profile if it doesn't exist
        customer = Customer.objects.create(
            user=request.user,
            customer_name=request.user.username,
            email=request.user.email
        )
        messages.info(request, "Customer profile created successfully.")
    
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        if product_id and quantity:
            try:
                product = Product.objects.get(pk=product_id)
                customer = request.user.customer
                cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)
                cart_item.quantity += int(quantity)
                if cart_item.quantity <= product.quantity_in_stock:
                    cart_item.save()
                    messages.success(request, f'{quantity} item(s) added to cart.')
                else:
                    messages.error(request, 'Requested quantity exceeds available stock.')
            except Product.DoesNotExist:
                messages.error(request, 'Product does not exist.')
        else:
            messages.error(request, 'Invalid request.')
    return redirect('cart')

@login_required
def delete_item_in_cart(request, id):
    cart_item = get_object_or_404(Cart, id=id, customer=request.user.customer)
    cart_item.delete()
    return redirect('cart')

@login_required
def increase_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity < cart_item.product.quantity_in_stock:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def generate_bill_number():
    """Generate a unique bill number with format: BILL-YYYYMMDD-XXXX"""
    from datetime import datetime
    import random
    import string
    
    date_str = datetime.now().strftime('%Y%m%d')
    # Generate a random 4-digit number
    random_digits = ''.join(random.choices(string.digits, k=4))
    return f'BILL-{date_str}-{random_digits}'
##changing checkout
@login_required
def checkout(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')
    
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    # Check if there's an exchange discount in the session
    exchange_value = request.session.get('exchange_value', 0)
    exchange_id = request.session.get('exchange_id')
    
    exchange_value_decimal = Decimal(str(exchange_value))
    # Adjust the total price with the exchange value
    final_price = max(0, total_price - exchange_value_decimal)
    
    if request.method == 'POST':
        address_id = request.POST.get('selected_address')
        
        if not address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('checkout')
            
        try:
            address = Address.objects.get(id=address_id, customer=customer)
            
            # Create order with adjusted total amount
            order = Order.objects.create(
                customer=customer,
                address=address,
                payment_method='cod',
                total_amount=final_price,
                status='Pending'
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # Update product stock
                item.product.quantity_in_stock -= item.quantity
                item.product.save()
            
            # If this is an exchange order, create an ExchangeOrder record
            if exchange_id:
                try:
                    exchange = TVExchange.objects.get(id=exchange_id, customer=customer)
                    ExchangeOrder.objects.create(
                        customer=customer,
                        exchange_request=exchange,
                        new_order=order,
                        exchange_value=exchange_value,
                        final_amount=final_price,
                        status='pending'
                    )
                    
                    # Update exchange status
                    exchange.status = 'completed'
                    exchange.save()
                    
                    # Clear exchange data from session
                    del request.session['exchange_id']
                    del request.session['exchange_value']
                    
                except TVExchange.DoesNotExist:
                    pass
            
            # Clear cart
            cart_items.delete()
            
            messages.success(request, "Order placed successfully! Your order is pending confirmation.")
            return redirect('order_tracking', order.id)
            
        except Address.DoesNotExist:
            messages.error(request, "Selected address not found.")
            return redirect('checkout')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('checkout')
    
    addresses = Address.objects.filter(customer=customer)
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'final_price': final_price,
        'exchange_value': exchange_value,
        'has_exchange': exchange_id is not None,
        'addresses': addresses,
    }
    return render(request, 'checkouts.html', context)

@login_required
def order_list(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer).order_by('-order_date')
    context = {
        'orders': orders,
    }
    return render(request, 'order_list.html', context)

@login_required
def cancel_order_item(request, item_id):
    if request.method == 'POST':
        try:
            # Get the order item
            item = get_object_or_404(OrderItem, id=item_id)
            
            # Check if the order belongs to the current user
            if item.order.customer != request.user.customer:
                messages.error(request, "You don't have permission to cancel this item.")
                return redirect('order_list')
            
            # Check if the order is in Pending status
            if item.order.status != 'Pending':
                messages.error(request, "Only pending orders can be canceled.")
                return redirect('order_list')
            
            # Check if the item is already canceled
            if item.canceled:
                messages.error(request, "This item is already canceled.")
                return redirect('order_list')
            
            # Cancel the item
            item.canceled = True
            item.save()
            
            # Update order total amount
            order = item.order
            order.total_amount = sum(item.total_price() for item in order.orderitem_set.filter(canceled=False))
            
            # If all items are canceled, update order status
            if not order.orderitem_set.filter(canceled=False).exists():
                order.status = 'Cancelled'
            
            order.save()
            messages.success(request, "Item canceled successfully.")
            
        except Exception as e:
            messages.error(request, f"Error canceling item: {str(e)}")
    
    return redirect('order_list')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'order_detail.html', context)

@login_required
def order_tracking(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user.customer)
        # Get the first order item for display
        order_item = order.orderitem_set.first()
        
        if not order_item:
            messages.error(request, "No items found in this order.")
            return redirect('order_list')
            
        context = {
            'order': order,
            'order_item': order_item,
        }
        return render(request, 'order_tracking.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order_list')

def product_list(request):
    products = Product.objects.all()  # Fetch all products
    categories = Category.objects.all()  # Fetch all categories
    return render(request, 'product_list.html', {
        'products': products,
        'categories': categories
    })


def search_results(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(subcategory__parent_category__category_name__icontains=query) |
            Q(subcategory__subcategory_name__icontains=query)
        ).distinct()
    else:
        products = Product.objects.none()

    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_list = []
        for product in products[:5]:  # Limit to 5 results for dropdown
            product_list.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'category': product.subcategory.parent_category.category_name if product.subcategory else '',
                'image': product.image_1.url if product.image_1 else '',
            })
        return JsonResponse(product_list, safe=False)

    # For normal requests, render the template
    context = {
        'query': query,
        'products': products,
    }
    return render(request, 'search_results.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(subcategory__parent_category=category)
    return render(request, 'category_products.html', {'category': category, 'products': products})

def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory)
    return render(request, 'subcategory_products.html', {'subcategory': subcategory, 'products': products})

# from .forms import PurchaseOrderForm

# def purchase_order(request):
#     products = None  # Initialize products to None
    
#     if request.method == 'POST':
#         form = PurchaseOrderForm(request.POST)
#         if form.is_valid():
#             selected_seller = form.cleaned_data['seller']
#             products = Product.objects.filter(seller=selected_seller)
#     else:
#         form = PurchaseOrderForm()

#     return render(request, 'purchase_order.html', {'form': form, 'products': products})

# from .forms import PurchaseForm


# def make_purchase(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     total_price = product.price  # Default total price to product price

#     if request.method == 'POST':
#         form = PurchaseForm(request.POST)
#         if form.is_valid():
#             quantity = form.cleaned_data['quantity']
#             total_price = product.price * quantity  # Calculate total price based on quantity
#             # Create purchase order
#             purchase_order = PurchaseOrder.objects.create(
#                 seller=product.seller,
#                 product=product,
#                 quantity=quantity,
#                 total_price=total_price
#             )
#             purchase_order.save()
#             return redirect('purchase_list')  # Redirect to purchase list page
#     else:
#         form = PurchaseForm()

#     return render(request, 'make_purchase.html', {'form': form, 'product': product, 'total_price': total_price})

# def purchase_list(request):
#     purchase_orders = PurchaseOrder.objects.all()
#     return render(request, 'purchase_list.html', {'purchase_orders': purchase_orders})


# class SellerLoginView(View):
#     def get(self, request):
#         return render(request, 'login.html')

#     def post(self, request):
#         email = request.POST['email']
#         password = request.POST['password']
#         user = authenticate(request, username=email, password=password)

#         if user is not None:
#             login(request, user)
#             return redirect('purchase_list')
#         else:
#             return render(request, 'login.html', {'error': 'Invalid credentials'})

def seller_purchase_orders(request):
    # Assuming you have a way to identify the current seller, e.g., request.user.seller
    seller = request.user.seller
    purchase_orders = PurchaseOrder.objects.filter(Seller=seller)
    return render(request, 'seller_purchase_orders.html', {'purchase_orders': purchase_orders})

from django.db import transaction

@transaction.atomic
def purchase_order_details(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    order_items = PurchaseOrderItem.objects.filter(PurchaseOrder=purchase_order)
    if request.method == 'POST':
        # Handle form submission to update delivery date and status
        delivery_date = request.POST.get('delivery_date')
        status = request.POST.get('status')
        # Update purchase order with new delivery date and status
        purchase_order.ExpectedDeliveryDate = delivery_date
        purchase_order.Status = status
        purchase_order.save()

        # Update product quantity if status is "Delivered"
        if status == 'Delivered':
            for item in order_items:
                item.Product.quantity_in_stock += item.Quantity
                item.Product.save()
        return redirect('seller_purchase_orders')

    return render(request, 'purchase_order_details.html', {'purchase_order': purchase_order, 'order_items': order_items})

def reject_purchase_order(request, purchase_order_id):
    if request.method == 'GET':
        seller_message = request.GET.get('seller_message', '')  # Get seller message from the query parameters
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)  # Get the purchase order object

        # Update purchase order status and seller message
        purchase_order.Status = 'Rejected'
        purchase_order.seller_message = seller_message
        purchase_order.save()

        return redirect('seller_purchase_orders')  # Redirect to seller purchase orders page
    
class CreatePurchaseOrderView(View):
    def get(self, request):
        sellers = Seller.objects.all()
        products = Product.objects.none()  # Initially empty

        if 'seller' in request.GET:
            seller_id = request.GET.get('seller')
            if seller_id:
                products = Product.objects.filter(seller_id=seller_id)
        
        context = {
            'sellers': sellers,
            'products': products,
        }
        return render(request, 'create_purchase_order.html', context)
    
    def post(self, request):
        seller_id = request.POST.get('seller')
        total_amount = request.POST.get('total_amount')

        # Get the selected seller
        selected_seller = Seller.objects.get(id=seller_id)

        # Create the PurchaseOrder object with the selected seller
        purchase_order = PurchaseOrder.objects.create(
            TotalAmount=total_amount,
            PurchaseOrderDate=date.today(),
            Seller=selected_seller,  # Assign the Seller object, not just the ID
        )

        # Save purchase order items
        for i in range(len(request.POST.getlist('product'))):
            product_id = request.POST.getlist('product')[i]
            product = Product.objects.get(id=product_id)
            quantity = request.POST.getlist('quantity')[i]
            purchase_unit_price = Product.objects.get(id=product_id).cost
            
            PurchaseOrderItem.objects.create(
                Product=product,
                Quantity=quantity,
                PurchaseUnitPrice=purchase_unit_price,
                PurchaseOrder=purchase_order,
            )

        return redirect('/admin/eapp/purchaseorder/')  # Redirect to a success page

@login_required
def payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user.customer)
        if order.payment_method == 'cod':
            messages.warning(request, "This order is Cash on Delivery. No payment required.")
            return redirect('order_detail', order_id)
            
        context = {
            'order': order
        }
        return render(request, 'payment.html', context)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order_list')

@login_required
def process_payment(request, order_id):
    if request.method != 'POST':
        return redirect('payment', order_id)
        
    try:
        order = Order.objects.get(id=order_id, customer=request.user.customer)
        
        if order.status == 'Paid':
            messages.warning(request, "This order has already been paid.")
            return redirect('order_detail', order_id)
            
        # Process card details (in a real app, you'd integrate with a payment gateway)
        card_number = request.POST.get('card_number')
        expiry = request.POST.get('expiry')
        cvv = request.POST.get('cvv')
        card_holder = request.POST.get('card_holder')
        
        if not all([card_number, expiry, cvv, card_holder]):
            messages.error(request, "Please fill in all card details.")
            return redirect('payment', order_id)
            
        # Update order status
        order.status = 'Paid'
        order.save()
        
        messages.success(request, "Payment successful! Thank you for your purchase.")
        return redirect('order_detail', order_id)
        
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order_list')
    except Exception as e:
        messages.error(request, f"Payment failed: {str(e)}")
        return redirect('payment', order_id)

@login_required
def generate_bill_pdf(request, order_id):
    # Get the order
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order_id}_bill.pdf"'
    
    # Create the PDF object using reportlab
    p = canvas.Canvas(response, pagesize=letter)
    
    # Add content to the PDF
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, 750, "PrimePixels")
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 720, f"Order Invoice #{order.id}")
    
    # Customer details
    p.setFont("Helvetica", 12)
    p.drawString(50, 690, f"Customer: {order.customer.user.get_full_name() or order.customer.user.username}")
    p.drawString(50, 670, f"Order Date: {order.order_date.strftime('%B %d, %Y')}")
    p.drawString(50, 650, f"Payment Method: {order.payment_method.upper()}")
    
    # Order items
    y = 600
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Product")
    p.drawString(300, y, "Quantity")
    p.drawString(400, y, "Price")
    p.drawString(500, y, "Total")
    
    y -= 20
    p.line(50, y, 550, y)
    y -= 20
    
    p.setFont("Helvetica", 12)
    for item in order.orderitem_set.all():
        if not item.canceled:
            p.drawString(50, y, item.product.name[:30])
            p.drawString(300, y, str(item.quantity))
            p.drawString(400, y, f"₹{item.product.price}")
            p.drawString(500, y, f"₹{item.total_price()}")
            y -= 20
    
    # Total
    y -= 20
    p.line(50, y, 550, y)
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, y, "Total Amount:")
    p.drawString(500, y, f"₹{order.total_amount}")
    
    # Finish the PDF
    p.showPage()
    p.save()
    return response

# Service Views
from .forms import ServiceAppointmentForm
def service_list(request):
    services = Service.objects.filter(is_available=True)
    context = {
        'services': services,
        'user_authenticated': request.user.is_authenticated
    }
    return render(request, 'services/service_list.html', context)

@login_required
def book_appointment(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    customer = request.user.customer
    
    # Initialize form with customer's addresses
    form = ServiceAppointmentForm()
    form.fields['address'].queryset = Address.objects.filter(customer=customer)
    
    if request.method == 'POST':
        form = ServiceAppointmentForm(request.POST)
        form.fields['address'].queryset = Address.objects.filter(customer=customer)
        
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.service = service
            appointment.customer = customer
            appointment.status = 'pending'
            appointment.payment_amount = service.price
            appointment.save()
            
            # Send email notification to admin
            subject = 'New Service Appointment'
            message = render_to_string('services/email/new_appointment_notification.html', {
                'appointment': appointment,
            })
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                html_message=message,
            )
            
            messages.success(request, 'Appointment booked successfully!')
            return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'services/book_appointment.html', {
        'service': service,
        'form': form
    })

@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id)
    
    if request.method == 'POST' and 'rating' in request.POST:
        rating = request.POST.get('rating')
        feedback = request.POST.get('feedback')
        if rating:
            appointment.customer_rating = rating
            appointment.customer_feedback = feedback
            appointment.save()
            
            # Update technician's rating
            if appointment.technician:
                technician = appointment.technician
                all_ratings = ServiceAppointment.objects.filter(
                    technician=technician,
                    customer_rating__isnull=False
                ).values_list('customer_rating', flat=True)
                if all_ratings:
                    technician.rating = sum(all_ratings) / len(all_ratings)
                    technician.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'services/appointment_detail.html', {
        'appointment': appointment
    })

@login_required
def process_service_payment(request, appointment_id):
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id)
    if appointment.customer != request.user.customer:
        messages.error(request, "You don't have permission to process this payment.")
        return redirect('appointment_list')
    
    if request.method == 'POST':
        # Process payment logic here
        # For now, we'll just mark it as completed
        appointment.payment_status = 'completed'
        appointment.status = 'confirmed'
        appointment.save()
        
        # Send confirmation email
        subject = 'Payment Confirmation - Service Appointment'
        message = render_to_string('services/email/payment_confirmation.html', {
            'appointment': appointment,
        })
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [appointment.customer.email],
            html_message=message,
        )
        
        messages.success(request, 'Payment processed successfully!')
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'services/process_payment.html', {
        'appointment': appointment
    })

# @login_required
# def technician_dashboard(request):
#     if not hasattr(request.user, 'technician'):
#         messages.error(request, "Access denied. You are not registered as a technician.")
#         return redirect('technician_login')
    
#     technician = request.user.technician
#     today = timezone.now().date()
    
#     # Get today's appointments
#     todays_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         appointment_date=today,
#         status__in=['pending', 'assigned', 'in_progress']
#     ).order_by('appointment_time')
    
#     # Get upcoming/assigned appointments
#     upcoming_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='assigned'
#     ).order_by('appointment_date', 'appointment_time')
    
#     # Get in-progress appointments
#     in_progress_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='in_progress'
#     ).order_by('appointment_date', 'appointment_time')
    
#     # Get completed appointments
#     completed_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='assigned'
#     ).order_by('-appointment_date', '-appointment_time')[:5]
    
#     # Get appointments with pending payments
#     pending_payment = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='completed',
#         payment_status='pending'
#     ).order_by('-appointment_date', '-appointment_time')
    
#     return render(request, 'services/technician_dashboard.html', {
#         'todays_appointments': todays_appointments,
#         'upcoming_appointments': upcoming_appointments,
#         'in_progress_appointments': in_progress_appointments,
#         'completed_appointments': completed_appointments,
#         'pending_payment': pending_payment,
#         'technician': technician
#     })
    
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def update_appointment_status(request, appointment_id):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')
    
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id, technician=request.user.technician)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        completion_notes = request.POST.get('completion_notes')
        
        if new_status in dict(ServiceAppointment.STATUS_CHOICES):
            appointment.status = new_status
            
            # If status is "Completed", update payment status
            if new_status == "Completed":
                appointment.payment_status = "Payment Pending"  # Update the field name based on your model
                
            if completion_notes:
                appointment.completion_notes = completion_notes
            appointment.save()
            
            # Send notification to customer
            subject = f'Service Appointment Status Update - {appointment.get_status_display()}'
            message = render_to_string('services/email/status_update.html', {
                'appointment': appointment,
            })
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [appointment.customer.email],
                html_message=message,
            )
            
            messages.success(request, 'Appointment status updated successfully!')
        else:
            messages.error(request, 'Invalid status provided.')
            
    return redirect('technician_dashboard')


@login_required
def appointment_list(request):
    appointments = ServiceAppointment.objects.filter(customer=request.user.customer)
    return render(request, 'services/appointment_list.html', {'appointments': appointments})

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(ServiceAppointment, id=appointment_id, customer=request.user.customer)
    if appointment.status == 'pending':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully!')
    else:
        messages.error(request, 'This appointment cannot be cancelled.')
    return redirect('appointment_list')

@login_required
def my_appointments(request):
    appointments = ServiceAppointment.objects.filter(
        customer=request.user.customer
    ).order_by('-appointment_date', '-appointment_time')
    
    return render(request, 'services/my_appointments.html', {
        'appointments': appointments
    })

def technician_login(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('email')  # Field name remains 'email' for backward compatibility
        password = request.POST.get('password')
        
        print(f"Login attempt with username/email: {username_or_email}")
        
        try:
            # Try to find user by email first
            user = User.objects.filter(email=username_or_email).first()
            
            # If not found by email, try username
            if user is None:
                user = User.objects.filter(username=username_or_email).first()
            
            if user is not None:
                # Now authenticate with the username and password
                authenticated_user = authenticate(request, username=user.username, password=password)
                print(f"Authentication result: {authenticated_user is not None}")
                
                if authenticated_user is not None:
                    if hasattr(authenticated_user, 'technician'):
                        print("User has technician profile")
                        login(request, authenticated_user)
                        messages.success(request, 'Welcome back!')
                        return redirect('technician_dashboard')
                    else:
                        print("User does not have technician profile")
                        messages.error(request, 'This account is not registered as a technician.')
                else:
                    print("Authentication failed")
                    messages.error(request, 'Invalid credentials.')
            else:
                print("No user found")
                messages.error(request, 'No account found with these credentials.')
        except Exception as e:
            print(f"Error during login: {str(e)}")
            messages.error(request, 'An error occurred during login.')
        
    return render(request, 'services/technician_login.html')

def about(request):
    return render(request, 'about.html')

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to view this page.")
        return redirect('index')
    
    # Get all appointments
    appointments = ServiceAppointment.objects.all().order_by('-appointment_date', '-appointment_time')
    
    # Get all technicians including those on leave
    technicians = Technician.objects.all().order_by('is_on_leave', 'name')
    
    # Separate active and on-leave technicians
    active_technicians = technicians.filter(is_on_leave=False)
    on_leave_technicians = technicians.filter(is_on_leave=True)
    
    # Get pending leave requests count
    pending_leave_requests = LeaveRequest.objects.filter(status='pending').count()
    
    # Get appointments by status
    pending_appointments = appointments.filter(status='pending')
    assigned_appointments = appointments.filter(status='assigned')
    in_progress_appointments = appointments.filter(status='in_progress')
    completed_appointments = appointments.filter(status='completed')
    cancelled_appointments = appointments.filter(status='cancelled')
    
    return render(request, 'services/admin_dashboard.html', {
        'appointments': appointments,
        'active_technicians': active_technicians,
        'on_leave_technicians': on_leave_technicians,
        'pending_leave_requests': pending_leave_requests,
        'pending_appointments': pending_appointments,
        'assigned_appointments': assigned_appointments,
        'in_progress_appointments': in_progress_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
    })

@login_required
def assign_technician(request, appointment_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to perform this action.")
        return redirect('index')
    
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id)
    
    if request.method == 'POST':
        technician_id = request.POST.get('technician')
        if technician_id:
            technician = get_object_or_404(Technician, pk=technician_id)
            # Check if technician is on leave
            if technician.is_on_leave:
                messages.error(request, f'Cannot assign appointment to {technician.name} as they are currently on leave')
                return redirect('assign_technician', appointment_id=appointment_id)
            
            appointment.technician = technician
            appointment.status = 'assigned'
            appointment.save()
            
            # Send email notification to technician
            subject = 'New Service Appointment Assigned'
            html_message = render_to_string('services/email/new_appointment_notification.html', {
                'appointment': appointment,
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [technician.user.email],
                html_message=html_message,
            )
            
            messages.success(request, f'Appointment assigned to {technician.name}')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please select a technician')
    
    # Get only active technicians (not on leave)
    available_technicians = Technician.objects.filter(is_on_leave=False)
    
    return render(request, 'services/assign_technician.html', {
        'appointment': appointment,
        'technicians': available_technicians,
    })

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def update_service_amount(request, appointment_id):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')
    
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id, technician=request.user.technician)
    
    if request.method == 'POST':
        service_amount = request.POST.get('service_amount')
        technician_notes = request.POST.get('technician_notes')
        
        try:
            appointment.service_amount = service_amount
            appointment.technician_notes = technician_notes
            appointment.save()
            messages.success(request, 'Service amount and notes updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating service amount: {str(e)}')
    
    return redirect('appointment_detail', appointment_id=appointment_id)

@login_required
def update_payment_status(request, appointment_id):
    # Check if the logged-in user is a technician
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')

    # Get the service appointment
    appointment = get_object_or_404(ServiceAppointment, id=appointment_id)

    # Ensure the appointment belongs to the current technician and is in the correct status
    if appointment.technician != request.user.technician:
        messages.error(request, "You are not authorized to update this appointment.")
        return redirect('index')

    # Only update if the payment status is pending
    if appointment.payment_status == 'pending':
        appointment.payment_status = 'completed'
        appointment.save()
        messages.success(request, "Payment status updated to 'Completed'.")
    else:
        messages.warning(request, "Payment status has already been updated.")

    return redirect('pending_payments')

@login_required
def request_leave(request):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('technician_login')
    
    # Get technician's leave history first
    try:
        leave_history = LeaveRequest.objects.filter(
            technician=request.user.technician
        ).order_by('-created_at')
    except Exception as e:
        messages.error(request, f"Error retrieving leave history: {str(e)}")
        leave_history = []
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        try:
            # Convert string dates to date objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Validate dates
            today = timezone.now().date()
            if start_date < today:
                messages.error(request, "Start date cannot be in the past.")
                return redirect('request_leave')
            
            if end_date < start_date:
                messages.error(request, "End date must be after start date.")
                return redirect('request_leave')
            
            # Check for overlapping leave requests
            existing_leaves = LeaveRequest.objects.filter(
                technician=request.user.technician,
                status__in=['pending', 'approved'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            if existing_leaves.exists():
                messages.error(request, "You already have a leave request for these dates.")
                return redirect('request_leave')
            
            # Create leave request
            leave_request = LeaveRequest.objects.create(
                technician=request.user.technician,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )
            
            messages.success(request, "Leave request submitted successfully.")
            return redirect('technician_dashboard')
            
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
        except Exception as e:
            messages.error(request, f"Error submitting leave request: {str(e)}")
    
    return render(request, 'services/request_leave.html', {
        'leave_history': leave_history
    })

@login_required
def manage_leave_requests(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('index')
    
    leave_requests = LeaveRequest.objects.all().select_related('technician')
    
    if request.method == 'POST':
        leave_request_id = request.POST.get('leave_request_id')
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id)
            
            if action == 'approve':
                leave_request.status = 'approved'
                message = "Leave request approved."
            elif action == 'reject':
                leave_request.status = 'rejected'
                message = "Leave request rejected."
            
            leave_request.admin_remarks = remarks
            leave_request.save()
            
            messages.success(request, message)
            
            # Send email notification to technician
            subject = f'Leave Request {leave_request.status.title()}'
            message = f"""
            Dear {leave_request.technician.name},
            
            Your leave request for {leave_request.start_date} to {leave_request.end_date} has been {leave_request.status}.
            
            Admin Remarks: {remarks if remarks else 'No remarks provided'}
            
            Best regards,
            Admin Team
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [leave_request.technician.user.email],
                fail_silently=True,
            )
            
        except LeaveRequest.DoesNotExist:
            messages.error(request, "Leave request not found.")
        except Exception as e:
            messages.error(request, f"Error processing leave request: {str(e)}")
    
    return render(request, 'services/manage_leave_requests.html', {
        'leave_requests': leave_requests
    })

@login_required
def add_technician(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to perform this action.")
        return redirect('index')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        expertise = request.POST.get('expertise')
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Create user account
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create technician profile
            technician = Technician.objects.create(
                user=user,
                name=name,
                phone_number=phone_number,
                expertise=expertise,
                is_available=True,
                is_on_leave=False
            )
            
            messages.success(request, f'Technician {name} has been added successfully')
            return redirect('admin_dashboard')
            
        except Exception as e:
            if 'user' in locals():
                user.delete()
            messages.error(request, f'Error creating technician: {str(e)}')
    
    return render(request, 'services/add_technician.html')

@login_required
def update_technician_fee(request, appointment_id):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')
    
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id, technician=request.user.technician)
    
    if request.method == 'POST':
        technician_fee = request.POST.get('technician_fee')
        completion_notes = request.POST.get('completion_notes')
        
        try:
            appointment.technician_fee = float(technician_fee)
            appointment.completion_notes = completion_notes
            appointment.save()
            messages.success(request, 'Service fee and notes updated successfully')
        except ValueError:
            messages.error(request, 'Please enter a valid amount for the service fee')
        except Exception as e:
            messages.error(request, f'Error updating service fee: {str(e)}')
    
    return redirect('appointment_detail', appointment_id=appointment_id)

# @login_required
# def technician_dashboard(request):
#     if not hasattr(request.user, 'technician'):
#         messages.error(request, "Access denied. You are not registered as a technician.")
#         return redirect('index')
    
#     technician = request.user.technician
    
#     # Get appointments assigned to this technician
#     assigned_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='assigned'
#     ).order_by('appointment_date', 'appointment_time')
    
#     in_progress_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='in_progress'
#     ).order_by('appointment_date', 'appointment_time')
    
#     completed_appointments = ServiceAppointment.objects.filter(
#         technician=technician,
#         status='completed'
#     ).order_by('-appointment_date', '-appointment_time')
    
#     context = {
#         'technician': technician,
#         'assigned_appointments': assigned_appointments,
#         'in_progress_appointments': in_progress_appointments,
#         'completed_appointments': completed_appointments,
#     }
    
#     return render(request, 'services/technician_dashboard.html', context)

@login_required
def pending_payments(request):
    # Check if the logged-in user is a technician
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')

    # Filter appointments assigned to the logged-in technician and with payment_status == "pending"
    pending_appointments = ServiceAppointment.objects.filter(
        technician=request.user.technician,
        status="completed",  # Looks like you only want completed ones
        payment_status="pending"
    )

    return render(request, 'services/pending_payments.html', {
        'pending_appointments': pending_appointments,
    })


@login_required
def completed_payments(request):
    # Check if the logged-in user is a technician
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')

    # Filter appointments assigned to the logged-in technician and with payment_status == "Complete"
    completed_appointments = ServiceAppointment.objects.filter(
        technician=request.user.technician,
        payment_status="completed"
    )

    return render(request, 'services/completed_payments.html', {
        'completed_appointments': completed_appointments,
    })

from django.shortcuts import render


@login_required
def update_technician_fee(request, appointment_id):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')
    
    appointment = get_object_or_404(ServiceAppointment, pk=appointment_id, technician=request.user.technician)
    
    if request.method == 'POST':
        technician_fee = request.POST.get('technician_fee')
        completion_notes = request.POST.get('completion_notes')
        
        try:
            appointment.technician_fee = float(technician_fee)
            appointment.completion_notes = completion_notes
            appointment.save()
            messages.success(request, 'Service fee and notes updated successfully')
        except ValueError:
            messages.error(request, 'Please enter a valid amount for the service fee')
        except Exception as e:
            messages.error(request, f'Error updating service fee: {str(e)}')
    
    return redirect('appointment_detail', appointment_id=appointment_id)

@login_required
def technician_dashboard(request):
    if not hasattr(request.user, 'technician'):
        messages.error(request, "Access denied. You are not registered as a technician.")
        return redirect('index')
    
    technician = request.user.technician
    
    # Get appointments assigned to this technician
    assigned_appointments = ServiceAppointment.objects.filter(
        technician=technician,
        status='assigned'
    ).order_by('appointment_date', 'appointment_time')
    
    in_progress_appointments = ServiceAppointment.objects.filter(
        technician=technician,
        status='in_progress'
    ).order_by('appointment_date', 'appointment_time')
    
    completed_appointments = ServiceAppointment.objects.filter(
        technician=technician,
        status='completed'
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'technician': technician,
        'assigned_appointments': assigned_appointments,
        'in_progress_appointments': in_progress_appointments,
        'completed_appointments': completed_appointments,
    }
    
    return render(request, 'services/technician_dashboard.html', context)

@login_required
def manage_technicians(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to view this page.")
        return redirect('index')
    
    technicians = Technician.objects.all().order_by('name')
    leave_requests = LeaveRequest.objects.all().order_by('-created_at')
    pending_leave_requests = leave_requests.filter(status='pending')
    
    if request.method == 'POST':
        leave_request_id = request.POST.get('leave_request_id')
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        leave_request = get_object_or_404(LeaveRequest, id=leave_request_id)
        
        if action == 'approve':
            leave_request.status = 'approved'
            leave_request.admin_remarks = remarks
            leave_request.save()
            
            # Update technician's leave status
            leave_request.technician.is_on_leave = True
            leave_request.technician.save()
            
            messages.success(request, f"Leave request for {leave_request.technician.name} has been approved.")
            
        elif action == 'reject':
            leave_request.status = 'rejected'
            leave_request.admin_remarks = remarks
            leave_request.save()
            messages.success(request, f"Leave request for {leave_request.technician.name} has been rejected.")
        
        return redirect('manage_technicians')
    
    return render(request, 'services/technician_management.html', {
        'technicians': technicians,
        'leave_requests': leave_requests,
        'pending_leave_requests': pending_leave_requests,
    })

@login_required
def edit_technician(request, technician_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to edit technicians.")
        return redirect('index')
    
    technician = get_object_or_404(Technician, id=technician_id)
    
    if request.method == 'POST':
        technician.name = request.POST.get('name')
        technician.phone_number = request.POST.get('phone_number')
        technician.email = request.POST.get('email')
        technician.expertise = request.POST.get('expertise')
        technician.save()
        
        messages.success(request, f"Technician {technician.name} updated successfully.")
        return redirect('manage_technicians')
    
    return redirect('manage_technicians')

@login_required
def schedule_leave(request, technician_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. You must be an admin to schedule leave.")
        return redirect('index')
    
    technician = get_object_or_404(Technician, id=technician_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        # Check for overlapping leave requests
        overlapping_leave = LeaveRequest.objects.filter(
            technician=technician,
            status='approved',
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if overlapping_leave:
            messages.error(request, "There is already an approved leave request for this period.")
            return redirect('manage_technicians')
        
        # Create and auto-approve leave request
        leave_request = LeaveRequest.objects.create(
            technician=technician,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status='approved',
            admin_remarks='Scheduled by admin'
        )
        
        # Update technician status
        technician.is_on_leave = True
        technician.save()
        
        messages.success(request, f"Leave scheduled for {technician.name} from {start_date} to {end_date}.")
        return redirect('manage_technicians')
    
    return redirect('manage_technicians')

@login_required
def delete_technicians(request):
    if request.method == 'POST':
        technician_ids = request.POST.get('technician_ids', '').split(',')
        Technician.objects.filter(id__in=technician_ids).delete()
        messages.success(request, f'Successfully deleted {len(technician_ids)} technician(s)')
    return redirect('manage_technicians')

@login_required
def manage_technicians(request):
    if request.method == 'POST':
        # Handle adding new technician
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        expertise = request.POST.get('expertise')
        
        Technician.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            expertise=expertise,
            is_available=True
        )
        messages.success(request, 'Technician added successfully')
        return redirect('manage_technicians')

    # Get filters
    expertise = request.GET.get('expertise')
    is_available = request.GET.get('is_available')
    
    # Start with all technicians
    technicians = Technician.objects.all()
    
    # Apply filters
    if expertise:
        technicians = technicians.filter(expertise=expertise)
    if is_available is not None:
        is_available = is_available.lower() == 'true'
        technicians = technicians.filter(is_available=is_available)
    
    context = {
        'technicians': technicians,
    }
    return render(request, 'services/technician_management.html', context)

@login_required
def approve_leave(request, leave_id):
    if request.method == 'POST':
        leave = get_object_or_404(LeaveRequest, id=leave_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            leave.status = 'approved'
            leave.technician.is_available = False
            leave.technician.save()
            messages.success(request, f'Leave approved for {leave.technician.name}')
        elif action == 'reject':
            leave.status = 'rejected'
            messages.success(request, f'Leave rejected for {leave.technician.name}')
        
        leave.save()
    return redirect('manage_technicians')

@login_required
def manage_technicians(request):
    if request.method == 'POST':
        # Handle adding new technician
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        expertise = request.POST.get('expertise')
        
        Technician.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            expertise=expertise,
            is_available=True
        )
        messages.success(request, 'Technician added successfully')
        return redirect('manage_technicians')

    # Get filters
    expertise = request.GET.get('expertise')
    is_available = request.GET.get('is_available')
    
    # Start with all technicians
    technicians = Technician.objects.all()
    
    # Apply filters
    if expertise:
        technicians = technicians.filter(expertise=expertise)
    if is_available is not None:
        is_available = is_available.lower() == 'true'
        technicians = technicians.filter(is_available=is_available)
    
    # Get pending leave requests
    pending_leaves = LeaveRequest.objects.filter(status='pending')
    
    context = {
        'technicians': technicians,
        'pending_leaves': pending_leaves,
    }
    return render(request, 'services/technician_management.html', context)

# TV Exchange Views
@login_required
def initiate_exchange(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    customer = get_object_or_404(Customer, user=request.user)
    
    if request.method == 'POST':
        # Calculate exchange value based on TV condition and age
        base_value = float(request.POST.get('original_price'))
        condition_multiplier = {
            'excellent': 0.5,
            'good': 0.4,
            'fair': 0.3,
            'poor': 0.2
        }
        age_deduction = min(int(request.POST.get('age_in_years')) * 0.1, 0.5)  # Max 50% deduction for age
        exchange_value = base_value * (condition_multiplier[request.POST.get('condition')] - age_deduction)
        exchange_value = max(exchange_value, 0)  # Ensure non-negative value
        
        exchange = TVExchange.objects.create(
            customer=customer,
            product=product,
            brand=request.POST.get('brand'),
            model=request.POST.get('model'),
            age_in_years=request.POST.get('age_in_years'),
            condition=request.POST.get('condition'),
            screen_size=request.POST.get('screen_size'),
            original_price=request.POST.get('original_price'),
            exchange_value=exchange_value,
            images=request.FILES.get('tv_image')
        )
        
        messages.success(request, 'Exchange details submitted successfully! Please review and confirm.')
        return redirect('exchange_detail', exchange_id=exchange.id)
        
    return render(request, 'exchange/initiate_exchange.html', {'product': product})

@login_required
def exchange_detail(request, exchange_id):
    exchange = get_object_or_404(TVExchange, id=exchange_id, customer__user=request.user)
    return render(request, 'exchange/exchange_detail.html', {'exchange': exchange})

@login_required
def exchange_checkout(request, exchange_id):
    if request.method == 'POST':
        exchange = get_object_or_404(TVExchange, id=exchange_id, customer__user=request.user)
        
        # Remove status check to allow checkout regardless of status
        customer = request.user.customer
        product = exchange.product
        exchange_value = exchange.exchange_value
        
        # Create a cart item with the product (or update if exists)
        cart_item, created = Cart.objects.get_or_create(
            customer=customer,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Store exchange information in session for checkout
        request.session['exchange_id'] = exchange_id
        request.session['exchange_value'] = float(exchange_value)
        
        messages.success(request, f"Product added to cart with exchange discount of ₹{exchange_value}")
        return redirect('checkout')
    
    return redirect('exchange_detail', exchange_id=exchange_id)

@login_required
def cancel_exchange(request, exchange_id):
    exchange = get_object_or_404(TVExchange, id=exchange_id, customer__user=request.user)
    if request.method == 'POST':
        exchange.status = 'cancelled'
        exchange.save()
        messages.success(request, 'Exchange request cancelled successfully.')
        return redirect('my_exchanges')
    return redirect('exchange_detail', exchange_id=exchange.id)

@login_required
def schedule_pickup(request, exchange_id):
    exchange = get_object_or_404(TVExchange, id=exchange_id, customer__user=request.user)
    if request.method == 'POST':
        if 'address_id' in request.POST:
            address = get_object_or_404(Address, id=request.POST['address_id'], customer__user=request.user)
            pickup_date = request.POST.get('pickup_date')
            time_slot = request.POST.get('time_slot')
            
            # Get or create pickup record
            pickup, created = ExchangePickup.objects.get_or_create(
                exchange=exchange,
                defaults={
                    'address': address,
                    'pickup_date': pickup_date,
                    'time_slot': time_slot,
                    'status': 'scheduled'
                }
            )
            
            # If pickup already existed, update its details
            if not created:
                pickup.address = address
                pickup.pickup_date = pickup_date
                pickup.time_slot = time_slot
                pickup.status = 'scheduled'
                pickup.save()
            
            # Update exchange status
            exchange.status = 'pending_pickup'
            exchange.save()
            
            messages.success(request, 'Pickup scheduled successfully!')
            return redirect('exchange_detail', exchange_id=exchange.id)
            
    addresses = Address.objects.filter(customer__user=request.user)
    return render(request, 'exchange/schedule_pickup.html', {
        'exchange': exchange,
        'addresses': addresses,
        'today': timezone.now().date()
    })

@login_required
def my_exchanges(request):
    exchanges = TVExchange.objects.filter(customer__user=request.user).order_by('-created_at')
    return render(request, 'exchange/my_exchanges.html', {'exchanges': exchanges})

# Admin views for TV Exchange
@login_required
def admin_exchange_list(request):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('index')
        
    exchanges = TVExchange.objects.all().order_by('-created_at')
    return render(request, 'admin/exchange_list.html', {'exchanges': exchanges})

@login_required
def admin_exchange_detail(request, exchange_id):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('index')
        
    exchange = get_object_or_404(TVExchange, id=exchange_id)
    pickup = ExchangePickup.objects.filter(exchange=exchange).first()
    
    if request.method == 'POST':
        status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes')
        
        exchange.status = status
        exchange.admin_notes = admin_notes
        exchange.save()
        
        if status == 'approved' and not pickup:
            messages.info(request, 'Please assign a technician for pickup')
            return redirect('assign_pickup_technician', exchange_id=exchange.id)
            
        messages.success(request, 'Exchange status updated successfully')
        
    return render(request, 'admin/exchange_detail.html', {
        'exchange': exchange,
        'pickup': pickup
    })

@login_required
def assign_pickup_technician(request, exchange_id):
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('index')
        
    exchange = get_object_or_404(TVExchange, id=exchange_id)
    pickup = get_object_or_404(ExchangePickup, exchange=exchange)
    
    if request.method == 'POST':
        technician_id = request.POST.get('technician')
        technician = get_object_or_404(Technician, id=technician_id)
        
        pickup.technician = technician
        pickup.save()
        
        # Send notification to technician
        subject = 'New TV Exchange Pickup Assignment'
        message = render_to_string('emails/pickup_assignment.html', {
            'technician': technician,
            'pickup': pickup,
            'exchange': exchange
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [technician.user.email],
            html_message=message
        )
        
        messages.success(request, 'Technician assigned successfully')
        return redirect('admin_exchange_detail', exchange_id=exchange.id)
    
    available_technicians = Technician.objects.filter(is_available=True, is_on_leave=False)
    return render(request, 'admin/assign_pickup_technician.html', {
        'exchange': exchange,
        'pickup': pickup,
        'technicians': available_technicians
    })

@login_required
def add_address(request):
    customer = get_object_or_404(Customer, user=request.user)
    if request.method == 'POST':
        street_address = request.POST.get('street_address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        
        address = Address.objects.create(
            customer=customer,
            street_address=street_address,
            city=city,
            state=state,
            pincode=pincode
        )
        
        # If this is from exchange pickup, redirect back
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        
        messages.success(request, 'Address added successfully!')
        return redirect('address_list')
        
    return render(request, 'address/add_address.html')
