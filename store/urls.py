from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("category/<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/confirmation/", views.order_confirmation, name="order_confirmation"),
    path("orders/", views.order_history, name="order_history"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="store/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("health/", views.health, name="health"),
]
