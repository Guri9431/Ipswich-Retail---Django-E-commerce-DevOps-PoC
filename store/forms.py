from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .cart import MAX_QTY_PER_LINE
from .models import Order


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=MAX_QTY_PER_LINE, initial=1)
    override = forms.BooleanField(required=False, widget=forms.HiddenInput)


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "email", "address", "city", "postcode"]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
