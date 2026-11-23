from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('sales-dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('product-sales-report/', views.product_sales_report, name='product_sales_report'),
    path('customer-management/', views.customer_management, name='customer_management'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

    path('register/', views.customer_register, name='register'),
    path('login/', views.customer_login, name='login'),
    path('logout/', views.customer_logout, name='logout'),
    path('my-account/', views.my_account, name='my_account'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-details/<int:order_id>/', views.order_details, name='order_details'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),

    path('stock-management/', views.stock_management, name='stock_management'),
    path('admin-order-management/', views.admin_order_management, name='admin_order_management'),

    # PRODUCT MANAGEMENT
    path('admin/add-product/', views.add_product, name='add_product'),
    path('admin/products/', views.product_management, name='product_management'),
    path('admin/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
]