from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from shop.models import Product


class Command(BaseCommand):
    help = 'Seeds Buyzeno with demo users and products.'

    def handle(self, *args, **options):
        user_model = get_user_model()

        admin_user, admin_created = user_model.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@buyzeno.local',
                'first_name': 'Buyzeno',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if admin_created:
            admin_user.set_password('Admin@12345')
            admin_user.save()

        demo_user, demo_created = user_model.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@buyzeno.local',
                'first_name': 'Demo',
                'last_name': 'Shopper',
            },
        )
        if demo_created:
            demo_user.set_password('Demo@12345')
            demo_user.save()

        catalog = [
            {
                'name': 'Auraloop Headphones',
                'description': 'Wireless headphones with rich spatial sound, soft memory foam, and a clean modern profile.',
                'price': '129.00',
                'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1200&q=80',
                'stock': 12,
                'featured': True,
            },
            {
                'name': 'Nova Carry Backpack',
                'description': 'A weather-ready commuter backpack with laptop protection, quick-access pockets, and elegant utility.',
                'price': '84.00',
                'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80',
                'stock': 7,
                'featured': True,
            },
            {
                'name': 'Solstice Smartwatch',
                'description': 'Track workouts, sleep, and notifications with a polished smartwatch built for daily performance.',
                'price': '219.00',
                'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1200&q=80',
                'stock': 5,
                'featured': True,
            },
            {
                'name': 'Lumen Desk Lamp',
                'description': 'A sculpted ambient lamp with warm brightness control designed to elevate workspaces.',
                'price': '59.00',
                'image': 'https://images.unsplash.com/photo-1519710164239-da123dc03ef4?auto=format&fit=crop&w=1200&q=80',
                'stock': 18,
                'featured': True,
            },
            {
                'name': 'Terra Ceramic Bottle',
                'description': 'A premium insulated bottle with soft-touch grip and all-day temperature retention.',
                'price': '34.00',
                'image': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=1200&q=80',
                'stock': 22,
                'featured': False,
            },
            {
                'name': 'Cinder Running Shoes',
                'description': 'Lightweight trainers that blend breathable comfort, shock support, and bold athletic styling.',
                'price': '149.00',
                'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80',
                'stock': 9,
                'featured': False,
            },
            {
                'name': 'Orbit Keyboard',
                'description': 'A tactile mechanical keyboard with refined acoustics and an ultra-clean workstation silhouette.',
                'price': '99.00',
                'image': 'https://images.unsplash.com/photo-1517336714739-489689fd1ca8?auto=format&fit=crop&w=1200&q=80',
                'stock': 14,
                'featured': False,
            },
            {
                'name': 'Velora Lounge Chair',
                'description': 'Curved statement seating built for cozy reading sessions and sharp interior styling.',
                'price': '299.00',
                'image': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80',
                'stock': 3,
                'featured': False,
            },
        ]

        created_count = 0
        for item in catalog:
            _, created = Product.objects.update_or_create(
                name=item['name'],
                defaults=item,
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS('Buyzeno demo data is ready.'))
        self.stdout.write('Admin login: admin / Admin@12345')
        self.stdout.write('Customer login: demo / Demo@12345')
        self.stdout.write(f'Products added or refreshed: {len(catalog)}')
