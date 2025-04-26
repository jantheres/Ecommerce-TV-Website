from django import forms
from .models import Address, Seller, ServiceAppointment, TVExchange, ExchangePickup, ExchangeOrder
from datetime import datetime, timedelta

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['recepient_name', 'recepient_contact', 'address_line1', 'address_line2', 'city', 'state', 'postal_code']
        widgets = {
            'recepient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Name'}),
            'recepient_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Contact'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
        }

# class PurchaseOrderForm(forms.Form):
#     seller = forms.ModelChoiceField(queryset=Seller.objects.all(), empty_label="Select Seller")

# class PurchaseForm(forms.Form):
#     quantity = forms.IntegerField(min_value=1, label='Quantity')

# class SellerLoginForm(forms.Form):
#     email = forms.EmailField(label='Email')
#     password = forms.CharField(label='Password', widget=forms.PasswordInput)

class ServiceAppointmentForm(forms.ModelForm):
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': datetime.now().date().isoformat()
        })
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    address = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    special_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions for the service technician?'
        })
    )

    class Meta:
        model = ServiceAppointment
        fields = ['appointment_date', 'appointment_time', 'address', 'special_instructions']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'customer'):
            self.fields['address'].queryset = user.customer.address_set.all()

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if appointment_date and appointment_time:
            # Check if appointment is in the past
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            if appointment_datetime < datetime.now():
                raise forms.ValidationError("Appointment cannot be in the past")

            # Check if appointment is within business hours (9 AM to 6 PM)
            if appointment_time.hour < 9 or appointment_time.hour >= 18:
                raise forms.ValidationError("Appointments are only available between 9 AM and 6 PM")

        return cleaned_data


from django import forms

class PaymentMethodForm(forms.Form):
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('paypal', 'PayPal'),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)
    transaction_id = forms.CharField(max_length=255, required=True, label='Transaction ID')
    amount_paid = forms.DecimalField(max_digits=10, decimal_places=2, required=True, label='Amount Paid')
    payment_date = forms.DateField(widget=forms.SelectDateWidget, required=True, label='Payment Date')

class TVExchangeForm(forms.ModelForm):
    class Meta:
        model = TVExchange
        fields = ['brand', 'model', 'age_in_years', 'condition', 'screen_size', 'original_price', 'images']
        widgets = {
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'TV Brand (e.g., Samsung, LG, Sony)'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'TV Model Number'
            }),
            'age_in_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age in Years',
                'min': '0',
                'max': '20'
            }),
            'condition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'screen_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Screen Size (e.g., 32, 43, 55)'
            }),
            'original_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Original Purchase Price'
            }),
            'images': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean_age_in_years(self):
        age = self.cleaned_data.get('age_in_years')
        if age < 0:
            raise forms.ValidationError("Age cannot be negative")
        if age > 20:
            raise forms.ValidationError("TVs older than 20 years are not eligible for exchange")
        return age

    def clean_original_price(self):
        price = self.cleaned_data.get('original_price')
        if price <= 0:
            raise forms.ValidationError("Original price must be greater than 0")
        return price

class ExchangePickupForm(forms.ModelForm):
    class Meta:
        model = ExchangePickup
        fields = ['address', 'pickup_date', 'time_slot']
        widgets = {
            'address': forms.Select(attrs={
                'class': 'form-control'
            }),
            'pickup_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': datetime.now().date().isoformat()
            }),
            'time_slot': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'customer'):
            self.fields['address'].queryset = user.customer.address_set.all()

    def clean_pickup_date(self):
        pickup_date = self.cleaned_data.get('pickup_date')
        if pickup_date < datetime.now().date():
            raise forms.ValidationError("Pickup date cannot be in the past")
        
        # Check if pickup date is within next 7 days
        max_date = datetime.now().date() + timedelta(days=7)
        if pickup_date > max_date:
            raise forms.ValidationError("Pickup must be scheduled within the next 7 days")
        
        return pickup_date

class ExchangeQualityCheckForm(forms.Form):
    QUALITY_CHECK_RESULT = [
        (True, 'Pass'),
        (False, 'Fail')
    ]
    
    quality_check_result = forms.ChoiceField(
        choices=QUALITY_CHECK_RESULT,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    quality_check_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter detailed notes about the TV condition and any issues found'
        }),
        required=True
    )

class ExchangeOrderForm(forms.ModelForm):
    class Meta:
        model = ExchangeOrder
        fields = ['exchange_value', 'final_amount', 'estimated_delivery_date']
        widgets = {
            'exchange_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'final_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'estimated_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': (datetime.now() + timedelta(days=1)).date().isoformat()
            })
        }

    def clean_estimated_delivery_date(self):
        delivery_date = self.cleaned_data.get('estimated_delivery_date')
        if delivery_date < datetime.now().date():
            raise forms.ValidationError("Delivery date cannot be in the past")
        return delivery_date
