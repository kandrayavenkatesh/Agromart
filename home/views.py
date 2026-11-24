from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .models import Product, Order, OrderItem, ProductReview, Wishlist, ContactMessage
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum, F, DecimalField, ExpressionWrapper, Count
from django.core.mail import send_mail
from .models import Coupon
from .models import CustomerProfile
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from .forms import ProductForm

def home(request):
    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '')

    products = Product.objects.all()
    print("TOTAL PRODUCTS:", products.count())
    products = products.annotate(
    average_rating=Avg('reviews__rating')
)

    if search_query:
        products = products.filter(
            name__icontains=search_query
        )

    if selected_category:
        products = products.filter(
            category__iexact=selected_category
        )

    
    if sort_by == 'low':
        products = products.order_by('price')

    elif sort_by == 'high':
        products = products.order_by('-price')
    
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    print("PRODUCTS BEFORE RENDER:", products.count())
    homepage_products = list(products)
    print("HOMEPAGE PRODUCTS:", len(homepage_products))

    return render(request, 'home.html', {
        'products': products,
        'homepage_products': homepage_products,
        'search_query': search_query,
        'selected_category': selected_category,
        'sort_by': sort_by,
        'cart_count': cart_count
    })


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    product_id = str(product_id)

    current_quantity = cart.get(product_id, 0)

    if product.stock <= 0:
        return redirect('home')

    if current_quantity >= product.stock:
        return redirect('cart')

    cart[product_id] = current_quantity + 1

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')

def view_cart(request):
    cart = request.session.get('cart', {})

    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id))

        subtotal = product.price * quantity
        total += subtotal

        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'cart.html', {
        'products': products,
        'total': total,
    })
    
def remove_from_cart(request, product_id):

    cart = request.session.get('cart', {}) 

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart

    return redirect('cart')

def increase_quantity(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:

        current_quantity = cart[product_id]

        if current_quantity < product.stock:
            cart[product_id] += 1

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    request.session['cart'] = cart

    return redirect('cart') 
 
def checkout(request):

    cart = request.session.get('cart', {})
    coupon_discount = Decimal(str(request.session.get('coupon_discount', '0.00'))
)
    coupon_code = request.session.get('coupon_code', '')

    products = []
    total = 0
    original_total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=int(product_id))

        subtotal = product.price * quantity
        original_total += subtotal

        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })
        total = max(
    original_total - coupon_discount,
    Decimal('0.00')
)

    if request.method == 'POST':

        if not products:
            return redirect('home')

        # CHECK AVAILABLE STOCK
        for item in products:
            if item['quantity'] > item['product'].stock:
                return render(request, 'checkout.html', {
                    'products': products,
                    'total': total,
                    'error': (
                        f"Not enough stock for "
                        f"{item['product'].name}. "
                        f"Available stock: {item['product'].stock}"
                    )
                })

        # CREATE ORDER
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            total_amount=total
        )

        # CREATE ORDER ITEMS AND REDUCE STOCK
        for item in products:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

            item['product'].stock -= item['quantity']
            item['product'].save()
        send_mail(
    subject=f'AgroMart Order Confirmation - Order #{order.id}',
    message=(
        f'Hello {order.name},\n\n'
        f'Thank you for shopping with AgroMart!\n'
        f'Your order #{order.id} has been placed successfully.\n'
        f'Total Amount: Rs. {order.total_amount}\n'
        f'Order Status: {order.status}\n\n'
        f'Thank you for choosing AgroMart!'
    ),
    from_email=None,
    recipient_list=[order.email],
    fail_silently=True,
)

        request.session['cart'] = {}
        request.session.pop('coupon_discount', None)
        request.session.pop('coupon_code', None)
        request.session.pop('coupon_error', None)

        return render(request, 'order_success.html', {
            'order': order
        })

    return render(request, 'checkout.html', {
        'products': products,
        'total': total,
    })
def customer_register(request):

    mobile_error = ''

    if request.method == 'POST':

        form = UserCreationForm(request.POST)
        mobile = request.POST.get('mobile', '').strip()

        if not mobile.isdigit() or len(mobile) != 10:
            mobile_error = 'Enter a valid 10-digit mobile number.'

        elif CustomerProfile.objects.filter(mobile=mobile).exists():
            mobile_error = 'This mobile number is already registered.'

        elif form.is_valid():

            user = form.save()

            user.first_name = request.POST.get(
                'first_name', ''
            ).strip()

            user.save()

            CustomerProfile.objects.create(
                user=user,
                mobile=mobile
            )

            login(request, user)

            return redirect('home')

    else:
        form = UserCreationForm()

    return render(request, 'register.html', {
        'form': form,
        'mobile_error': mobile_error
    })

def customer_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


@login_required
def my_account(request):
    return render(request, 'my_account.html')


def customer_logout(request):
    if request.method == 'POST':
        logout(request)

    return redirect('home')

@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'my_orders.html', {
        'orders': orders
    })

@login_required
def order_details(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request,
'order_details.html', {
        'order': order
    })
@login_required
def cancel_order(request, order_id):

    if request.method == 'POST':

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

        if order.status in ['Pending', 'Confirmed']:

            # RESTORE PRODUCT STOCK
            order_items = OrderItem.objects.filter(order=order)

            for item in order_items:

                product = item.product

                product.stock += item.quantity

                product.save()

            # UPDATE ORDER STATUS
            order.status = 'Cancelled'
            order.save()

    return redirect('my_orders')

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment', '').strip()

        if 1 <= rating <= 5 and comment:
            ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )

            return redirect('product_detail', product_id=product.id)

    reviews = ProductReview.objects.filter(
        product=product
    ).order_by('-created_at')
    related_products = Product.objects.exclude(
    id=product.id
)[:4]

    return render(request, 'product_detail.html', {
    'product': product,
    'reviews': reviews,
    'related_products': related_products
})

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('home')

@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return redirect('wishlist')

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)

    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items
    })

@login_required
def edit_profile(request):

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')

        request.user.save()

        return redirect('my_account')

    return render(request, 'edit_profile.html')

@login_required
def change_password(request):

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('my_account')

    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'change_password.html', {
        'form': form
    })
def contact(request):

    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message')
        )

        return render(request, 'contact.html', {
            'success': True
        })

    return render(request, 'contact.html')
def about(request):
    return render(request, 'about.html')
def faq(request):
    return render(request, 'faq.html')
@staff_member_required
def admin_dashboard(request):

    total_products = Product.objects.count()

    total_stock = Product.objects.aggregate(
        total=Sum('stock')
    )['total'] or 0

    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=5
    )

    out_of_stock_products = Product.objects.filter(
        stock=0
    )

    return render(request, 'admin_dashboard.html', {
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
    })

@staff_member_required
def sales_dashboard(request):

    total_orders = Order.objects.count()

    total_revenue = Order.objects.exclude(
        status='Cancelled'
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    pending_orders = Order.objects.filter(
        status='Pending'
    ).count()

    delivered_orders = Order.objects.filter(
        status='Delivered'
    ).count()

    cancelled_orders = Order.objects.filter(
        status='Cancelled'
    ).count()

    return render(request, 'sales_dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
    })

@staff_member_required
def product_sales_report(request):

    product_sales = OrderItem.objects.exclude(
        order__status='Cancelled'
    ).values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2
                )
            )
        )
    ).order_by('-total_quantity')

    return render(request, 'product_sales_report.html', {
        'product_sales': product_sales
    })
    
@staff_member_required
def customer_management(request):

    search = request.GET.get('search', '').strip()

    customers = User.objects.filter(
        is_staff=False,
        is_superuser=False
    ).annotate(
        total_orders=Count('orders')
    ).order_by('-date_joined', '-id')

    # Search by username, email or first name
    if search:
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search)
        )

    # Total matching customers before pagination
    total_customers = customers.count()

    # Pagination: 10 customers per page
    paginator = Paginator(customers, 10)

    page_number = request.GET.get('page')

    customers_page = paginator.get_page(page_number)

    return render(request, 'customer_management.html', {
        'customers': customers_page,
        'search_query': search,
        'total_customers': total_customers,
    })
@staff_member_required
def stock_management(request):

    products = Product.objects.all().order_by('name')

    if request.method == 'POST':

        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')

        product = get_object_or_404(
            Product,
            id=product_id
        )

        if new_stock and new_stock.isdigit():
            product.stock = int(new_stock)
            product.save()

        return redirect('stock_management')

    return render(request, 'stock_management.html', {
        'products': products
    })
def apply_coupon(request):

    if request.method == 'POST':

        code = request.POST.get('coupon_code', '').strip().upper()

        cart = request.session.get('cart', {})
        original_total = Decimal('0.00')

        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=int(product_id))
            original_total += product.price * quantity

        try:
            coupon = Coupon.objects.get(
                code=code,
                active=True,
                expiry_date__gte=timezone.now()
            )

            if original_total < coupon.minimum_amount:
                request.session['coupon_error'] = (
                    f"Minimum order amount is ₹{coupon.minimum_amount}"
                )
                request.session.pop('coupon_discount', None)
                request.session.pop('coupon_code', None)

            else:
                discount = (
                    original_total * coupon.discount_percentage / Decimal('100')
                )

                request.session['coupon_discount'] = str(discount)
                request.session['coupon_code'] = coupon.code
                request.session.pop('coupon_error', None)

        except Coupon.DoesNotExist:
            request.session['coupon_error'] = 'Invalid or expired coupon code.'
            request.session.pop('coupon_discount', None)
            request.session.pop('coupon_code', None)

    return redirect('checkout')

@staff_member_required
def admin_order_management(request):

    allowed_statuses = [
        'Pending',
        'Confirmed',
        'Processing',
        'Shipped',
        'Delivered',
        'Cancelled'
    ]

    # UPDATE ORDER STATUS
    if request.method == 'POST':

        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')

        if new_status in allowed_statuses:

            order = get_object_or_404(Order, id=order_id)

            if order.status != 'Cancelled':

                # CANCEL ORDER AND RESTORE STOCK
                if new_status == 'Cancelled':

                    if order.status in ['Pending', 'Confirmed']:

                        with transaction.atomic():

                            order_items = OrderItem.objects.filter(
                                order=order
                            ).select_related('product')

                            for item in order_items:

                                product = item.product
                                product.stock += item.quantity
                                product.save(update_fields=['stock'])

                            order.status = 'Cancelled'
                            order.save(update_fields=['status'])

                else:

                    order.status = new_status
                    order.save(update_fields=['status'])

        # Preserve search, filter and page after updating
        return_query = request.POST.get('return_query', '')

        if return_query:
            return redirect(
                request.path + '?' + return_query
            )

        return redirect('admin_order_management')


    # ALL ORDERS
    all_orders = Order.objects.all()

    # ORDER STATISTICS
    order_statistics = all_orders.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='Pending')),
        confirmed=Count('id', filter=Q(status='Confirmed')),
        processing=Count('id', filter=Q(status='Processing')),
        shipped=Count('id', filter=Q(status='Shipped')),
        delivered=Count('id', filter=Q(status='Delivered')),
        cancelled=Count('id', filter=Q(status='Cancelled'))
    )


    # SEARCH ORDERS
    orders = all_orders.order_by('id')

    search_query = request.GET.get('search', '').strip()

    if search_query:

        search_filter = (
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

        if search_query.isdigit():
            search_filter |= Q(id=int(search_query))

        orders = orders.filter(search_filter)


    # FILTER BY STATUS
    status_filter = request.GET.get('status', '')

    if status_filter in allowed_statuses:
        orders = orders.filter(status=status_filter)


    # TOTAL MATCHING ORDERS
    filtered_order_count = orders.count()


    # PAGINATION
    paginator = Paginator(orders, 10)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)


    return render(request, 'admin_order_management.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_orders': order_statistics['total'],
        'pending_orders': order_statistics['pending'],
        'confirmed_orders': order_statistics['confirmed'],
        'processing_orders': order_statistics['processing'],
        'shipped_orders': order_statistics['shipped'],
        'delivered_orders': order_statistics['delivered'],
        'cancelled_orders': order_statistics['cancelled'],
        'filtered_order_count': filtered_order_count,
        'allowed_statuses': allowed_statuses,
        'return_query': request.GET.urlencode(),
    })
@staff_member_required
def add_product(request):

    if request.method == 'POST':

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()

            return redirect('add_product')

    else:
        form = ProductForm()

    return render(request, 'add_product.html', {
        'form': form
    })
# PRODUCT MANAGEMENT

@staff_member_required
def product_management(request):

    # GET ALL PRODUCTS
    products = Product.objects.all()

    # SEARCH PRODUCTS
    search_query = request.GET.get('search', '').strip()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # FILTER BY CATEGORY
    category_filter = request.GET.get('category', '')

    if category_filter:
        products = products.filter(
            category=category_filter
        )

    # SORT PRODUCTS
    sort_by = request.GET.get('sort', 'id')

    allowed_sort_options = [
        'id', '-id',
        'name', '-name',
        'price', '-price',
        'stock', '-stock'
    ]

    if sort_by not in allowed_sort_options:
        sort_by = 'id'

    products = products.order_by(sort_by)

    # CATEGORY LIST
    categories = Product.objects.values_list(
        'category',
        flat=True
    ).distinct().order_by('category')

    # PAGINATION
    paginator = Paginator(products, 10)

    page_obj = paginator.get_page(
        request.GET.get('page')
    )

    return render(request, 'product_management.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
    })


@staff_member_required
def add_product(request):

    if request.method == 'POST':

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Product added successfully!'
            )

            return redirect('product_management')

    else:
        form = ProductForm()

    return render(request, 'add_product.html', {
        'form': form
    })


@staff_member_required
def edit_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == 'POST':

        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Product updated successfully!'
            )

            return redirect('product_management')

    else:
        form = ProductForm(instance=product)

    return render(request, 'edit_product.html', {
        'form': form,
        'product': product
    })


@staff_member_required
def delete_product(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == 'POST':

        try:
            product.delete()

            messages.success(
                request,
                'Product deleted successfully!'
            )

            return redirect('product_management')

        except ProtectedError:

            return render(
                request,
                'confirm_delete_product.html',
                {
                    'product': product,
                    'error_message': (
                        'This product cannot be deleted because '
                        'it is linked to existing orders.'
                    )
                }
            )

    return render(request, 'confirm_delete_product.html', {
        'product': product
    })