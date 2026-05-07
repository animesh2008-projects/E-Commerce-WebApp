from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders_view, name='orders'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/products/new/', views.admin_product_create, name='admin_product_create'),
    path('dashboard/products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('dashboard/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('dashboard/products/<int:pk>/stock/', views.admin_product_stock_update, name='admin_product_stock_update'),
    path('dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/products/<slug:slug>/', views.api_product_detail, name='api_product_detail'),
    path('api/cart/', views.api_cart, name='api_cart'),
    path('api/cart/add/<int:product_id>/', views.add_to_cart, name='api_add_to_cart'),
    path('api/cart/update/<int:item_id>/', views.update_cart_item, name='api_update_cart_item'),
    path('api/cart/remove/<int:item_id>/', views.remove_cart_item, name='api_remove_cart_item'),
    path('api/orders/', views.api_orders, name='api_orders'),
    path('api/orders/place/', views.checkout, name='api_place_order'),
    path('api/admin/products/', views.api_admin_products, name='api_admin_products'),
    path('api/admin/products/create/', views.api_admin_product_create, name='api_admin_product_create'),
    path('api/admin/products/<int:pk>/', views.api_admin_product_detail, name='api_admin_product_detail'),
    path('api/admin/orders/', views.api_admin_orders, name='api_admin_orders'),
    path('api/admin/orders/<int:pk>/status/', views.api_admin_order_status, name='api_admin_order_status'),
    path('api/admin/users/', views.api_admin_users, name='api_admin_users'),
]
