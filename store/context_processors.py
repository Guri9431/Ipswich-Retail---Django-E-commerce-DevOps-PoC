from .cart import Cart
from .models import Category


def cart(request):
    return {"cart": Cart(request), "nav_categories": Category.objects.all()}
