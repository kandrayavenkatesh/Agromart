from django.contrib import admin
from .models import Product, Order, OrderItem, ProductReview, Wishlist, ContactMessage, Coupon

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock', 'image')
    search_fields = ('name',)
    list_filter = ('category',)
    fields = ('name', 'category', 'description', 'price', 'image', 'stock')
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'phone',
        'email',
        'total_amount',
        'status',
        'created_at'
    )

    search_fields = ('name', 'phone', 'email')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)

    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')

admin.site.register(ProductReview)
admin.site.register(Wishlist)
admin.site.register(ContactMessage)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        'code',
        'discount_percentage',
        'minimum_amount',
        'expiry_date',
        'active'
    )

    search_fields = ('code',)

    list_filter = ('active', 'expiry_date')