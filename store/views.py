import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import AddToCartForm, CheckoutForm, RegisterForm
from .models import Category, Order, OrderItem, Product

logger = logging.getLogger("store")


# --- Catalogue (pages 1 & 2) -------------------------------------------------
def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(available=True).select_related("category")
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    page = Paginator(products, 8).get_page(request.GET.get("page"))
    return render(request, "store/product_list.html", {"category": category, "page": page, "query": query})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, "store/product_detail.html", {"product": product, "form": AddToCartForm()})


# --- Cart (page 3) ----------------------------------------------------------
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    form = AddToCartForm(request.POST)
    if form.is_valid() and product.in_stock:
        Cart(request).add(product, form.cleaned_data["quantity"], form.cleaned_data["override"])
        messages.success(request, f"{product.name} added to your basket.")
    else:
        messages.error(request, "Could not add that item (out of stock or invalid quantity).")
    return redirect("store:cart_detail")


@require_POST
def cart_remove(request, product_id):
    Cart(request).remove(get_object_or_404(Product, id=product_id))
    return redirect("store:cart_detail")


def cart_detail(request):
    return render(request, "store/cart.html", {"form": AddToCartForm()})


# --- Checkout (page 4) ------------------------------------------------------
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, "Your basket is empty.")
        return redirect("store:product_list")

    initial = {}
    if request.user.is_authenticated:
        initial = {"full_name": request.user.get_full_name(), "email": request.user.email}
    form = CheckoutForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()
                for item in cart:
                    product = Product.objects.select_for_update().get(pk=item["product"].pk)
                    if product.stock < item["quantity"]:
                        raise ValueError(f"Insufficient stock for {product.name}")
                    product.stock -= item["quantity"]
                    product.save(update_fields=["stock"])
                    OrderItem.objects.create(
                        order=order, product=product, price=item["price"], quantity=item["quantity"]
                    )
                order.status = Order.Status.PAID  # PoC: payment is simulated
                order.save(update_fields=["status"])
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("store:cart_detail")
        cart.clear()
        logger.info("order_created id=%s total=%s", order.pk, order.total)
        return redirect("store:order_confirmation", order_id=order.pk)

    return render(request, "store/checkout.html", {"form": form})


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # Only the owner (or the same browser session that just ordered) may view it.
    if order.user_id and order.user_id != request.user.id:
        return redirect("store:product_list")
    return render(request, "store/order_confirmation.html", {"order": order})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related("items__product")
    return render(request, "store/order_history.html", {"orders": orders})


# --- Accounts ---------------------------------------------------------------
def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Ipswich Retail!")
        return redirect("store:product_list")
    return render(request, "store/register.html", {"form": form})


# --- Ops endpoints ----------------------------------------------------------
def health(request):
    """Liveness/readiness probe used by Docker HEALTHCHECK, CI smoke tests and Render."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok", "database": "ok"})
    except Exception:  # pragma: no cover - defensive
        logger.exception("health_check_failed")
        return JsonResponse({"status": "error", "database": "down"}, status=503)
