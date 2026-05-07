from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CartItem, Order, Product


class BuyzenoFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='shopper',
            email='shopper@example.com',
            password='StrongPass123',
        )
        self.admin = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='StrongPass123',
            is_staff=True,
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='A product used for test coverage.',
            price='49.99',
            stock=10,
            featured=True,
        )

    def test_storefront_pages_render(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to Buyzeno')

        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_product_api_returns_product(self):
        response = self.client.get(reverse('api_products'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['products'][0]['name'], self.product.name)

    def test_authenticated_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username='shopper', password='StrongPass123')
        add_response = self.client.post(
            reverse('add_to_cart', args=[self.product.id]),
            {'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)

        checkout_response = self.client.post(
            reverse('checkout'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(checkout_response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_admin_dashboard_requires_staff(self):
        self.client.login(username='shopper', password='StrongPass123')
        forbidden = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(forbidden.status_code, 403)

        self.client.login(username='manager', password='StrongPass123')
        allowed = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(allowed.status_code, 200)

# Create your tests here.
