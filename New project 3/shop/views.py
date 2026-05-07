import json
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .forms import LoginForm, OrderStatusForm, ProductForm, RegistrationForm
from .models import CartItem, Order, OrderItem, Product


def wants_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')


def parse_payload(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return {}
    return request.POST


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
        if not request.user.is_staff:
            if wants_json(request):
                return JsonResponse({'message': 'Admin access required.'}, status=403)
            return HttpResponseForbidden('Admin access required.')
        return view_func(request, *args, **kwargs)

    return wrapped


def currency(value):
    return f'{value:.2f}'


def serialize_product(product):
    return {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': currency(product.price),
        'image': product.image,
        'stock': product.stock,
        'stock_status': product.stock_label,
        'featured': product.featured,
        'created_at': product.created_at.isoformat(),
    }


def serialize_cart_item(item):
    return {
        'id': item.id,
        'product_id': item.product_id,
        'name': item.product.name,
        'price': currency(item.product.price),
        'quantity': item.quantity,
        'line_total': currency(item.line_total),
        'stock': item.product.stock,
        'image': item.product.image,
        'slug': item.product.slug,
    }


def serialize_order(order):
    return {
        'id': order.id,
        'user': order.user.username,
        'status': order.status,
        'total_price': currency(order.total_price),
        'created_at': order.created_at.isoformat(),
        'items': [
            {
                'product': item.product.name,
                'quantity': item.quantity,
                'price': currency(item.price),
                'line_total': currency(item.line_total),
            }
            for item in order.items.select_related('product')
        ],
    }


def cart_snapshot(user):
    items = list(
        CartItem.objects.filter(user=user)
        .select_related('product')
        .order_by('-updated_at')
    )
    total = sum(item.line_total for item in items)
    count = sum(item.quantity for item in items)
    return {
        'items': items,
        'item_count': count,
        'total': total,
    }


def home(request):
    featured_products = Product.objects.filter(featured=True)[:4]
    latest_products = Product.objects.all()[:8]
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
    }
    return render(request, 'storefront/home.html', context)


def product_list(request):
    query = request.GET.get('q', '').strip()
    availability = request.GET.get('availability', '')
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if availability == 'in-stock':
        products = products.filter(stock__gt=0)
    elif availability == 'low-stock':
        products = products.filter(stock__gt=0, stock__lte=5)
    elif availability == 'out-of-stock':
        products = products.filter(stock=0)

    return render(
        request,
        'storefront/products.html',
        {
            'products': products,
            'query': query,
            'availability': availability,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(pk=product.pk)[:4]
    return render(
        request,
        'storefront/product_detail.html',
        {
            'product': product,
            'related_products': related_products,
        },
    )


@login_required
def cart_view(request):
    snapshot = cart_snapshot(request.user)
    return render(
        request,
        'storefront/cart.html',
        {
            'cart_items': snapshot['items'],
            'cart_count': snapshot['item_count'],
            'cart_total': snapshot['total'],
        },
    )


@login_required
def orders_view(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )
    return render(request, 'storefront/orders.html', {'orders': orders})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your Buyzeno account is ready to go.')
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Welcome back to Buyzeno.')
            return redirect(request.GET.get('next') or 'home')
    else:
        form = LoginForm(request)

    return render(request, 'auth/login.html', {'form': form})


def cart_auth_guard(request):
    if request.user.is_authenticated:
        return None
    if wants_json(request):
        return JsonResponse(
            {
                'message': 'Sign in to add products to your cart.',
                'login_url': reverse('login'),
            },
            status=401,
        )
    return redirect(f"{reverse('login')}?next={request.path}")


@require_POST
def add_to_cart(request, product_id):
    guard_response = cart_auth_guard(request)
    if guard_response:
        return guard_response

    product = get_object_or_404(Product, pk=product_id)
    payload = parse_payload(request)
    try:
        quantity = max(1, int(payload.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    if product.stock == 0:
        error = {'message': 'This product is currently out of stock.'}
        if wants_json(request):
            return JsonResponse(error, status=400)
        messages.error(request, error['message'])
        return redirect('product_detail', slug=product.slug)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 0},
    )
    cart_item.quantity = min(cart_item.quantity + quantity, product.stock)
    cart_item.save(update_fields=['quantity', 'updated_at'])

    snapshot = cart_snapshot(request.user)
    message = 'Added to cart.' if created else 'Cart updated.'
    response_payload = {
        'message': message,
        'cart_count': snapshot['item_count'],
        'cart_total': currency(snapshot['total']),
        'item': serialize_cart_item(cart_item),
    }
    if wants_json(request):
        return JsonResponse(response_payload)

    messages.success(request, message)
    return redirect('cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related('product'),
        pk=item_id,
        user=request.user,
    )
    payload = parse_payload(request)
    try:
        quantity = int(payload.get('quantity', cart_item.quantity))
    except (TypeError, ValueError):
        quantity = cart_item.quantity

    quantity = max(1, min(quantity, cart_item.product.stock or 1))
    cart_item.quantity = quantity
    cart_item.save(update_fields=['quantity', 'updated_at'])

    snapshot = cart_snapshot(request.user)
    response_payload = {
        'message': 'Cart quantity updated.',
        'cart_count': snapshot['item_count'],
        'cart_total': currency(snapshot['total']),
        'item': serialize_cart_item(cart_item),
    }
    if wants_json(request):
        return JsonResponse(response_payload)

    messages.success(request, response_payload['message'])
    return redirect('cart')


@login_required
@require_POST
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related('product'),
        pk=item_id,
        user=request.user,
    )
    cart_item.delete()
    snapshot = cart_snapshot(request.user)
    response_payload = {
        'message': 'Item removed from cart.',
        'cart_count': snapshot['item_count'],
        'cart_total': currency(snapshot['total']),
    }
    if wants_json(request):
        return JsonResponse(response_payload)

    messages.success(request, response_payload['message'])
    return redirect('cart')


@login_required
@require_POST
def checkout(request):
    cart_items = list(
        CartItem.objects.filter(user=request.user).select_related('product')
    )
    if not cart_items:
        payload = {'message': 'Your cart is empty.'}
        if wants_json(request):
            return JsonResponse(payload, status=400)
        messages.error(request, payload['message'])
        return redirect('cart')

    with transaction.atomic():
        locked_products = {
            product.id: product
            for product in Product.objects.select_for_update().filter(
                id__in=[item.product_id for item in cart_items]
            )
        }
        order = Order.objects.create(user=request.user)
        running_total = Decimal('0.00')

        for cart_item in cart_items:
            product = locked_products[cart_item.product_id]
            if product.stock < cart_item.quantity:
                payload = {
                    'message': f'Only {product.stock} left for {product.name}.',
                }
                if wants_json(request):
                    return JsonResponse(payload, status=400)
                messages.error(request, payload['message'])
                return redirect('cart')

            product.stock -= cart_item.quantity
            product.save(update_fields=['stock'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=cart_item.quantity,
                price=product.price,
            )
            running_total += product.price * cart_item.quantity

        order.total_price = running_total
        order.save(update_fields=['total_price'])
        CartItem.objects.filter(user=request.user).delete()

    response_payload = {
        'message': f'Order #{order.pk} placed successfully.',
        'order_id': order.pk,
        'cart_count': 0,
        'cart_total': '0.00',
    }
    if wants_json(request):
        return JsonResponse(response_payload)

    messages.success(request, response_payload['message'])
    return redirect('orders')


@require_GET
def api_products(request):
    products = Product.objects.all()
    return JsonResponse({'products': [serialize_product(product) for product in products]})


@require_GET
def api_product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return JsonResponse({'product': serialize_product(product)})


@login_required
@require_GET
def api_cart(request):
    snapshot = cart_snapshot(request.user)
    return JsonResponse(
        {
            'items': [serialize_cart_item(item) for item in snapshot['items']],
            'cart_count': snapshot['item_count'],
            'cart_total': currency(snapshot['total']),
        }
    )


@login_required
@require_GET
def api_orders(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product')
        .order_by('-created_at')
    )
    return JsonResponse({'orders': [serialize_order(order) for order in orders]})


@admin_required
def admin_dashboard(request):
    total_sales = Order.objects.aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0.00')
    metrics = {
        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'users': User.objects.count(),
        'sales': total_sales,
    }
    low_stock_products = Product.objects.filter(stock__lte=5).order_by('stock', 'name')[:6]
    recent_orders = Order.objects.select_related('user').prefetch_related('items__product')[:6]
    return render(
        request,
        'admin_panel/dashboard.html',
        {
            'metrics': metrics,
            'low_stock_products': low_stock_products,
            'recent_orders': recent_orders,
        },
    )


@admin_required
def admin_products(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(
        request,
        'admin_panel/products.html',
        {
            'products': products,
            'query': query,
        },
    )


@admin_required
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully.')
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(
        request,
        'admin_panel/product_form.html',
        {
            'form': form,
            'page_title': 'Add Product',
            'submit_label': 'Create product',
        },
    )


@admin_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(
        request,
        'admin_panel/product_form.html',
        {
            'form': form,
            'page_title': f'Edit {product.name}',
            'submit_label': 'Save changes',
            'product': product,
        },
    )


@admin_required
@require_POST
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('admin_products')


@admin_required
@require_POST
def admin_product_stock_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        stock_value = max(0, int(request.POST.get('stock', product.stock)))
    except (TypeError, ValueError):
        stock_value = product.stock
    product.stock = stock_value
    product.save(update_fields=['stock'])
    messages.success(request, f'Stock updated for {product.name}.')
    return redirect('admin_products')


@admin_required
def admin_orders(request):
    orders = Order.objects.select_related('user').prefetch_related('items__product')

    if request.method == 'POST':
        order = get_object_or_404(Order, pk=request.POST.get('order_id'))
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order #{order.pk} updated.')
            return redirect('admin_orders')
    else:
        form = OrderStatusForm()

    return render(
        request,
        'admin_panel/orders.html',
        {
            'orders': orders,
            'status_form': form,
            'status_choices': Order.Status.choices,
        },
    )


@admin_required
def admin_users(request):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=request.POST.get('user_id'))
        if user != request.user:
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            state = 'reactivated' if user.is_active else 'blocked'
            messages.success(request, f'{user.username} has been {state}.')
        else:
            messages.error(request, 'You cannot block your own admin account.')
        return redirect('admin_users')

    users = User.objects.annotate(order_total=Count('orders')).order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {'users': users})


@admin_required
@require_GET
def api_admin_products(request):
    products = Product.objects.all()
    return JsonResponse({'products': [serialize_product(product) for product in products]})


@admin_required
def api_admin_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'GET':
        return JsonResponse({'product': serialize_product(product)})

    if request.method == 'DELETE':
        product.delete()
        return JsonResponse({'message': 'Product deleted.'})

    payload = parse_payload(request)
    form = ProductForm(payload, instance=product)
    if form.is_valid():
        updated_product = form.save()
        return JsonResponse(
            {
                'message': 'Product updated.',
                'product': serialize_product(updated_product),
            }
        )
    return JsonResponse({'errors': form.errors}, status=400)


@admin_required
@require_POST
def api_admin_product_create(request):
    payload = parse_payload(request)
    form = ProductForm(payload)
    if form.is_valid():
        product = form.save()
        return JsonResponse(
            {
                'message': 'Product created.',
                'product': serialize_product(product),
            },
            status=201,
        )
    return JsonResponse({'errors': form.errors}, status=400)


@admin_required
@require_GET
def api_admin_orders(request):
    orders = Order.objects.select_related('user').prefetch_related('items__product')
    return JsonResponse({'orders': [serialize_order(order) for order in orders]})


@admin_required
@require_POST
def api_admin_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    payload = parse_payload(request)
    form = OrderStatusForm(payload, instance=order)
    if form.is_valid():
        updated_order = form.save()
        return JsonResponse(
            {
                'message': 'Order updated.',
                'order': serialize_order(updated_order),
            }
        )
    return JsonResponse({'errors': form.errors}, status=400)


@admin_required
@require_GET
def api_admin_users(request):
    users = User.objects.annotate(order_total=Count('orders')).order_by('-date_joined')
    payload = {
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_admin': user.is_staff,
                'is_active': user.is_active,
                'orders': user.order_total,
            }
            for user in users
        ]
    }
    return JsonResponse(payload)
