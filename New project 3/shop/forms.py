from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Order, Product


class StyledFieldsMixin:
    default_class = 'form-control'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} {self.default_class}'.strip()
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-checkbox'


class RegistrationForm(StyledFieldsMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, label='First name')
    last_name = forms.CharField(max_length=150, label='Last name', required=False)
    email = forms.EmailField(label='Email address')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class LoginForm(StyledFieldsMixin, AuthenticationForm):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class ProductForm(StyledFieldsMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image', 'stock', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class OrderStatusForm(StyledFieldsMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
