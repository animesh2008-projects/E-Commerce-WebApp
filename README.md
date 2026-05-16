<img width="1920" height="1020" alt="Screenshot 2026-05-16 084924" src="https://github.com/user-attachments/assets/0a7e7abc-e5eb-4472-99e5-318a96429506" />
# E-Commerce-WebApp
# Buyzeno

Buyzeno is a modern full-stack Django e-commerce application with:

- Animated storefront pages
- Secure session-based authentication
- Product browsing and detail pages
- Dynamic cart interactions and checkout
- Order history for customers
- Admin dashboard for products, stock, orders, and users
- JSON APIs for products, cart, orders, and admin actions

## Quick Start

1. Run migrations:

```powershell
python manage.py migrate
```

2. Seed demo data:

```powershell
python manage.py seed_buyzeno
```

3. Start the server:

```powershell
python manage.py runserver
```

4. Open:

- Storefront: `http://127.0.0.1:8000/`
- Admin dashboard: `http://127.0.0.1:8000/dashboard/`
- Django admin: `http://127.0.0.1:8000/admin/`

## Demo Credentials

- Admin: `admin / Admin@12345`
- Customer: `demo / Demo@12345`

## Notes

- Because the project lives in a OneDrive-backed folder, SQLite is configured to store the database in `AppData\Local\Buyzeno\db.sqlite3` by default.
- You can override the database path with the `BUYZENO_DB_PATH` environment variable.

## Validation

```powershell
python manage.py check
python manage.py test
```
