from django import forms
from .models import Product


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            'name',
            'category',
            'description',
            'price',
            'image',
            'stock',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter product name'
            }),

            'category': forms.TextInput(attrs={
                'placeholder': 'Enter product category'
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Enter product description',
                'rows': 4
            }),

            'price': forms.NumberInput(attrs={
                'placeholder': 'Enter product price',
                'step': '0.01'
            }),

            'stock': forms.NumberInput(attrs={
                'placeholder': 'Enter available stock'
            }),
        }