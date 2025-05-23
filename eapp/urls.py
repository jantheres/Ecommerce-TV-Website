from django.urls import path
from . import views 



urlpatterns = [
    path('',views.index,name='index'),
    path('about/', views.about, name='about'),
    path('customer_dashboard/',views.customer_dashboard,name='customer_dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    # In eapp/urls.py
    path('order/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('order/<int:order_id>/bill/', views.generate_bill_pdf, name='generate_bill_pdf'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('logout/', views.user_logout, name='logout'),
    path('edit_customer/', views.edit_customer, name='edit_customer'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('address/', views.address_list, name='address_list'),
    path('address/create/', views.address_create, name='address_create'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.address_edit, name='address_edit'),
    path('address/delete/<int:address_id>/', views.address_delete, name='address_delete'),
    path("cart/", views.cart, name="cart"),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:cart_item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:cart_item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('delete_item_in_cart/<int:id>/', views.delete_item_in_cart, name='delete_item_in_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_list/', views.order_list, name='order_list'),
    path('order_tracking/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('product_list',views.product_list,name='product_list'),
    path('search/', views.search_results, name='search_results'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('subcategory/<int:subcategory_id>/', views.subcategory_products, name='subcategory_products'),
    path('create_purchase_order/', views.CreatePurchaseOrderView.as_view(), name='create_purchase_order'),
    path('seller/', views.seller_purchase_orders, name='seller_purchase_orders'),
    # path('seller/history', views.seller_purchase_orders_history, name='seller_purchase_orders_history'),
    path('seller/purchase_order/<int:purchase_order_id>/', views.purchase_order_details, name='purchase_order_details'),
    path('seller/purchase_order/<int:purchase_order_id>/reject/', views.reject_purchase_order, name='reject_purchase_order'),
    path('orders/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('process_payment/<int:order_id>/', views.process_payment, name='process_payment'),
    path('service_list/', views.service_list, name='service_list'),
    path('book_appointment/<int:service_id>/', views.book_appointment, name='book_appointment'),
    path('appointment_detail/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('process_service_payment/<int:appointment_id>/', views.process_service_payment, name='process_service_payment'),
    path('technician/login/', views.technician_login, name='technician_login'),
    path('technician/dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('technician/leave/request/', views.request_leave, name='request_leave'),
    path('admin/leave/manage/', views.manage_leave_requests, name='manage_leave_requests'),
    path('update_appointment_status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    path('update_technician_fee/<int:appointment_id>/', views.update_technician_fee, name='update_technician_fee'),
    # Service URLs
    path('services/', views.service_list, name='service_list'),
    path('services/appointments/', views.my_appointments, name='my_appointments'),
    path('services/<int:service_id>/book/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:appointment_id>/payment/', views.process_service_payment, name='process_service_payment'),
    
    # Technician URLs
    path('pending-payments/', views.pending_payments, name='pending_payments'),
    path('completed-payments/', views.completed_payments, name='completed_payments'),
    
    # TV Exchange URLs
    path('exchange/checkout/<int:exchange_id>/', views.exchange_checkout, name='exchange_checkout'),
    path('exchange/initiate/<int:product_id>/', views.initiate_exchange, name='initiate_exchange'),
    path('exchange/detail/<int:exchange_id>/', views.exchange_detail, name='exchange_detail'),
    path('exchange/pickup/<int:exchange_id>/', views.schedule_pickup, name='schedule_pickup'),
    path('exchange/my-exchanges/', views.my_exchanges, name='my_exchanges'),
    path('admin/exchanges/', views.admin_exchange_list, name='admin_exchange_list'),
    path('admin/exchanges/<int:exchange_id>/', views.admin_exchange_detail, name='admin_exchange_detail'),
    path('admin/exchanges/<int:exchange_id>/assign-technician/', views.assign_pickup_technician, name='assign_pickup_technician'),
    path('exchange/cancel/<int:exchange_id>/', views.cancel_exchange, name='cancel_exchange'),
    path('update-payment-status/<int:appointment_id>/', views.update_payment_status, name='update_payment_status'),
    path('technicians/', views.manage_technicians, name='manage_technicians'),
    path('technicians/delete/', views.delete_technicians, name='delete_technicians'),
    path('technicians/leave/<int:leave_id>/approve/', views.approve_leave, name='approve_leave'),
    path('admin/technicians/edit/<int:technician_id>/', views.edit_technician, name='edit_technician'),
    path('admin/technicians/schedule-leave/<int:technician_id>/', views.schedule_leave, name='schedule_leave'),
]
