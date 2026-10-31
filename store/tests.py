"""Automated tests run by the CI pipeline.

* Unit tests        - models and the Cart class in isolation
* Integration tests - views + templates + database working together
* End-to-end tests  - a full customer journey through the HTTP layer
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .cart import Cart
from .models import Category, Order, Product


def make_product(name="Test Coffee", price="5.00", stock=10, category=None, available=True):
    category = category or Category.objects.get_or_create(name="Test Cat", slug="test-cat")[0]
    return Product.objects.create(
        category=category,
        name=name,
        slug=name.lower().replace(" ", "-"),
        price=Decimal(price),
        stock=stock,
        available=available,
    )


# ---------------------------------------------------------------- unit tests
class ModelUnitTests(TestCase):
    def test_product_str_and_url(self):
        p = make_product()
        self.assertEqual(str(p), "Test Coffee")
        self.assertEqual(p.get_absolute_url(), reverse("store:product_detail", args=[p.slug]))

    def test_in_stock_property(self):
        self.assertTrue(make_product("A", stock=1).in_stock)
        self.assertFalse(make_product("B", stock=0).in_stock)
        self.assertFalse(make_product("C", stock=5, available=False).in_stock)

    def test_order_total(self):
        p = make_product(price="2.50")
        order = Order.objects.create(full_name="A", email="a@b.com", address="1 St", city="Ipswich", postcode="IP1 1AA")
        order.items.create(product=p, price=p.price, quantity=3)
        self.assertEqual(order.total, Decimal("7.50"))


class CartUnitTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.get(reverse("store:product_list"))  # creates a session
        self.request = type("R", (), {"session": self.client.session})()
        self.product = make_product(stock=5, price="4.00")

    def test_add_and_total(self):
        cart = Cart(self.request)
        cart.add(self.product, 2)
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart.total(), Decimal("8.00"))

    def test_quantity_capped_by_stock(self):
        cart = Cart(self.request)
        cart.add(self.product, 99)
        self.assertEqual(len(cart), 5)

    def test_override_and_remove(self):
        cart = Cart(self.request)
        cart.add(self.product, 3)
        cart.add(self.product, 1, override=True)
        self.assertEqual(len(cart), 1)
        cart.remove(self.product)
        self.assertEqual(len(cart), 0)


# ---------------------------------------------------------- integration tests
class CatalogueIntegrationTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Tea", slug="tea")
        self.p1 = make_product("Green Tea", category=self.cat)
        self.p2 = make_product("Hidden Tea", category=self.cat, available=False)

    def test_list_shows_available_only(self):
        r = self.client.get(reverse("store:product_list"))
        self.assertContains(r, "Green Tea")
        self.assertNotContains(r, "Hidden Tea")

    def test_category_filter_and_search(self):
        other = make_product("Mug", category=Category.objects.create(name="Kitchen", slug="kitchen"))
        r = self.client.get(reverse("store:product_list_by_category", args=["tea"]))
        self.assertContains(r, "Green Tea")
        self.assertNotContains(r, other.name)
        r = self.client.get(reverse("store:product_list"), {"q": "mug"})
        self.assertContains(r, "Mug")
        self.assertNotContains(r, "Green Tea")

    def test_detail_404_for_unavailable(self):
        self.assertEqual(self.client.get(self.p2.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(self.p1.get_absolute_url()).status_code, 200)

    def test_cart_requires_post(self):
        r = self.client.get(reverse("store:cart_add", args=[self.p1.id]))
        self.assertEqual(r.status_code, 405)

    def test_cart_add_out_of_stock_rejected(self):
        oos = make_product("Gone", stock=0)
        self.client.post(reverse("store:cart_add", args=[oos.id]), {"quantity": 1})
        r = self.client.get(reverse("store:cart_detail"))
        self.assertContains(r, "empty")

    def test_checkout_empty_cart_redirects(self):
        r = self.client.get(reverse("store:checkout"))
        self.assertRedirects(r, reverse("store:product_list"))

    def test_checkout_validation_errors(self):
        self.client.post(reverse("store:cart_add", args=[self.p1.id]), {"quantity": 1})
        r = self.client.post(reverse("store:checkout"), {"full_name": ""})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_order_history_requires_login(self):
        r = self.client.get(reverse("store:order_history"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("store:login"), r.url)

    def test_health_endpoint(self):
        r = self.client.get(reverse("store:health"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_metrics_endpoint_exposed(self):
        r = self.client.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"django_http_requests_total_by_method", r.content)


# ------------------------------------------------------------ end-to-end test
class EndToEndJourneyTests(TestCase):
    """Register -> browse -> add to basket -> checkout -> confirmation -> history."""

    def test_full_customer_journey(self):
        coffee = make_product("Journey Coffee", price="6.00", stock=10)
        tea = make_product("Journey Tea", price="3.50", stock=4)

        # 1. register (auto login)
        r = self.client.post(
            reverse("store:register"),
            {"username": "alice", "email": "alice@example.com", "password1": "S3cure!Pass99", "password2": "S3cure!Pass99"},
            follow=True,
        )
        self.assertContains(r, "Welcome to Ipswich Retail")

        # 2. browse and open a product page
        self.assertContains(self.client.get(reverse("store:product_list")), "Journey Coffee")
        self.assertEqual(self.client.get(coffee.get_absolute_url()).status_code, 200)

        # 3. add to basket
        self.client.post(reverse("store:cart_add", args=[coffee.id]), {"quantity": 2})
        self.client.post(reverse("store:cart_add", args=[tea.id]), {"quantity": 1})
        r = self.client.get(reverse("store:cart_detail"))
        self.assertContains(r, "15.50")  # 2*6.00 + 3.50

        # 4. checkout
        r = self.client.post(
            reverse("store:checkout"),
            {"full_name": "Alice Smith", "email": "alice@example.com", "address": "1 High St", "city": "Ipswich", "postcode": "IP1 1AA"},
            follow=True,
        )
        order = Order.objects.get()
        self.assertEqual(order.user.username, "alice")
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.total, Decimal("15.50"))
        self.assertContains(r, f"#{order.pk}")

        # 5. stock decremented and basket emptied
        coffee.refresh_from_db()
        tea.refresh_from_db()
        self.assertEqual((coffee.stock, tea.stock), (8, 3))
        self.assertContains(self.client.get(reverse("store:cart_detail")), "empty")

        # 6. order appears in history
        self.assertContains(self.client.get(reverse("store:order_history")), f"Order #{order.pk}")

    def test_login_logout_flow(self):
        User.objects.create_user("bob", "bob@example.com", "S3cure!Pass99")
        self.assertTrue(self.client.login(username="bob", password="S3cure!Pass99"))
        r = self.client.post(reverse("store:logout"), follow=True)
        self.assertContains(r, "Login")

    def test_stock_race_is_rejected(self):
        p = make_product("Last One", stock=1)
        self.client.post(reverse("store:cart_add", args=[p.id]), {"quantity": 1})
        Product.objects.filter(pk=p.pk).update(stock=0)  # someone else buys it first
        r = self.client.post(
            reverse("store:checkout"),
            {"full_name": "C", "email": "c@d.com", "address": "x", "city": "y", "postcode": "z"},
            follow=True,
        )
        self.assertContains(r, "Insufficient stock")
        self.assertEqual(Order.objects.count(), 0)


class SeedCommandTests(TestCase):
    def test_seed_is_idempotent(self):
        from django.core.management import call_command

        call_command("seed_data", verbosity=0)
        count = Product.objects.count()
        self.assertGreaterEqual(count, 12)
        call_command("seed_data", verbosity=0)
        self.assertEqual(Product.objects.count(), count)
        self.assertTrue(User.objects.filter(username="admin", is_superuser=True).exists())


class ProductImageTests(TestCase):
    def test_every_catalogue_image_exists_on_disk(self):
        from pathlib import Path

        from django.conf import settings
        from django.utils.text import slugify

        from .catalogue import CATALOGUE

        folder = Path(settings.BASE_DIR) / "store" / "static" / "store" / "products"
        self.assertTrue((folder / "placeholder.svg").exists())
        for items in CATALOGUE.values():
            for name, *_ in items:
                self.assertTrue((folder / f"{slugify(name)}.svg").exists(), f"missing image for {name}")

    def test_seed_sets_online_photo_but_keeps_custom_url(self):
        from django.core.management import call_command

        call_command("seed_data", verbosity=0)
        self.assertTrue(all(p.image_url.startswith("https://images.unsplash.com/") for p in Product.objects.all()))
        Product.objects.filter(slug="wool-throw-blanket").update(image_url="https://example.com/mine.jpg")
        Product.objects.filter(slug="bamboo-chopping-board").update(image_url="/static/store/products/bamboo-chopping-board.svg")
        call_command("seed_data", verbosity=0)
        self.assertEqual(Product.objects.get(slug="wool-throw-blanket").image_url, "https://example.com/mine.jpg")
        self.assertTrue(Product.objects.get(slug="bamboo-chopping-board").image_url.startswith("https://images.unsplash.com/"))

    def test_local_file_overrides_online_photo(self):
        from .models import PRODUCT_IMAGE_DIR

        p = make_product("Override Me", price="1.00")
        p.image_url = "https://example.com/online.jpg"
        p.save()
        self.assertEqual(p.image_src, "https://example.com/online.jpg")
        mine = PRODUCT_IMAGE_DIR / "override-me.png"
        mine.write_bytes(b"fake")
        try:
            self.assertTrue(p.image_src.endswith("/store/products/override-me.png"))
        finally:
            mine.unlink()
        self.assertEqual(p.image_src, "https://example.com/online.jpg")

    def test_fallback_is_product_svg_when_available(self):
        p = Product.objects.create(
            category=Category.objects.create(name="Kitchen", slug="kitchen"), name="Bamboo Chopping Board",
            slug="bamboo-chopping-board", price=Decimal("1.00"), stock=1,
        )
        self.assertTrue(p.fallback_src.endswith("/store/products/bamboo-chopping-board.svg"))

    def test_image_status_command_runs(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_data", verbosity=0)
        out = StringIO()
        call_command("image_status", stdout=out)
        self.assertIn("bamboo-chopping-board.jpg", out.getvalue())

    def test_image_src_falls_back_to_placeholder(self):
        p = make_product("No Image")
        self.assertTrue(p.image_src.endswith("placeholder.svg"))
