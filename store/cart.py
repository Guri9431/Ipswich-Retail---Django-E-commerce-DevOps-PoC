"""Session-backed shopping cart (kept out of views for modularity/testability)."""
from decimal import Decimal

from django.conf import settings

from .models import Product

MAX_QTY_PER_LINE = 20


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override=False):
        pid = str(product.id)
        current = self.cart.get(pid, {"quantity": 0, "price": str(product.price)})
        new_qty = quantity if override else current["quantity"] + quantity
        new_qty = max(0, min(new_qty, MAX_QTY_PER_LINE, product.stock))
        if new_qty == 0:
            self.remove(product)
            return
        current["quantity"] = new_qty
        current["price"] = str(product.price)
        self.cart[pid] = current
        self.save()

    def remove(self, product):
        self.cart.pop(str(product.id), None)
        self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session.pop(settings.CART_SESSION_ID, None)
        self.session.modified = True

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys())
        by_id = {str(p.id): p for p in products}
        for pid, item in list(self.cart.items()):
            product = by_id.get(pid)
            if product is None:  # product deleted since it was added
                continue
            price = Decimal(item["price"])
            yield {
                "product": product,
                "quantity": item["quantity"],
                "price": price,
                "total_price": price * item["quantity"],
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def total(self):
        return sum((Decimal(i["price"]) * i["quantity"] for i in self.cart.values()), Decimal("0.00"))
