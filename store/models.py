from decimal import Decimal

from pathlib import Path

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

PRODUCT_IMAGE_DIR = Path(settings.BASE_DIR) / "store" / "static" / "store" / "products"
LOCAL_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".avif")


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_list_by_category", args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image_url = models.CharField(max_length=300, blank=True, help_text="Full URL or /static/... path")
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["available", "name"])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])

    @property
    def local_image(self):
        """Your own picture: drop store/static/store/products/<slug>.jpg (or .png/.webp) to override."""
        for ext in LOCAL_IMAGE_EXTENSIONS:
            if (PRODUCT_IMAGE_DIR / f"{self.slug}{ext}").exists():
                return static(f"store/products/{self.slug}{ext}")
        return ""

    @property
    def fallback_src(self):
        """Generated SVG used when no other picture loads."""
        if (PRODUCT_IMAGE_DIR / f"{self.slug}.svg").exists():
            return static(f"store/products/{self.slug}.svg")
        return static("store/products/placeholder.svg")

    @property
    def image_src(self):
        # Priority: your local file -> Image url (online photo) -> generated SVG
        return self.local_image or self.image_url or self.fallback_src

    @property
    def in_stock(self):
        return self.available and self.stock > 0


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order #{self.pk}"

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.price * self.quantity
