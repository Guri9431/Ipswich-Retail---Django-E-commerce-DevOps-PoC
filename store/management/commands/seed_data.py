"""Seed demo catalogue + demo accounts. Idempotent, safe to run on every deploy."""
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.catalogue import CATALOGUE
from store.models import Category, Product

PHOTO_URL = "https://images.unsplash.com/{}?auto=format&fit=crop&w=600&q=70"


class Command(BaseCommand):
    help = "Create demo categories, products and users."

    def handle(self, *args, **options):
        created_products = 0
        for cat_name, items in CATALOGUE.items():
            category, _ = Category.objects.get_or_create(name=cat_name, defaults={"slug": slugify(cat_name)})
            for name, price, stock, desc, _emoji, photo in items:
                slug = slugify(name)
                product, created = Product.objects.get_or_create(
                    slug=slug,
                    defaults={"category": category, "name": name, "price": price, "stock": stock, "description": desc},
                )
                # Fill in the default online photo, but never overwrite a URL you set yourself.
                if not product.image_url or product.image_url.startswith("/static/store/products/"):
                    product.image_url = PHOTO_URL.format(photo)
                    product.save(update_fields=["image_url"])
                created_products += int(created)

        admin_user = os.environ.get("DEMO_ADMIN_USER", "admin")
        admin_pass = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin@12345")
        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(admin_user, "admin@ipswichretail.example", admin_pass)
            self.stdout.write(f"Created superuser '{admin_user}'")

        cust_user = os.environ.get("DEMO_CUSTOMER_USER", "customer")
        cust_pass = os.environ.get("DEMO_CUSTOMER_PASSWORD", "Customer@12345")
        if not User.objects.filter(username=cust_user).exists():
            User.objects.create_user(cust_user, "customer@ipswichretail.example", cust_pass)
            self.stdout.write(f"Created customer '{cust_user}'")

        self.stdout.write(self.style.SUCCESS(f"Seed complete ({created_products} new products)."))
