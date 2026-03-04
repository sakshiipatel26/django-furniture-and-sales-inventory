from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Return, Exchange
from .models import Product

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please explain why you want to return this product'
            })
        }

class ProductImageSelectWidget(forms.Select):
    def render_option(self, selected_choices, option_value, option_label):
        product = Product.objects.filter(id=option_value).first()
        image_url = product.image.url if product and product.image else ""
        return f'<option value="{option_value}" data-image="{image_url}">{option_label}</option>'

class ExchangeForm(forms.ModelForm):
    new_product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=ProductImageSelectWidget(attrs={"class": "form-control"}),
        label="Select New Product"
    )

    class Meta:
        model = Exchange
        fields = ["new_product", "reason"]