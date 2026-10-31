"""Show which picture each product uses and the exact filename to add your own."""
from django.core.management.base import BaseCommand

from store.models import PRODUCT_IMAGE_DIR, Product


class Command(BaseCommand):
    help = "List every product, the filename for a custom image, and which source is currently used."

    def handle(self, *args, **options):
        self.stdout.write(f"Put your images in: {PRODUCT_IMAGE_DIR}\n")
        self.stdout.write(f"{'PRODUCT':<40} {'FILENAME TO ADD (.jpg/.png/.webp)':<48} CURRENT SOURCE")
        for p in Product.objects.order_by("name"):
            source = "your local file" if p.local_image else ("image_url" if p.image_url else "generated fallback")
            self.stdout.write(f"{p.name:<40} {p.slug + '.jpg':<48} {source}")
