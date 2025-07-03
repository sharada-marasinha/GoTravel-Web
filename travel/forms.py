from django import forms
from django.contrib.auth.models import User
from .models import Booking, Review, UserProfile

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['travel_date', 'return_date', 'num_people', 'special_requests']
        widgets = {
            'travel_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'num_people': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PackageSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search packages...'})
    )
    destination = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Destinations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    package_type = forms.ChoiceField(
        choices=[('', 'All Types')] + [('tour', 'Tour'), ('hotel', 'Hotel'), ('transport', 'Transport'), ('combo', 'Combo')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Price'})
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Price'})
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Destination
        super().__init__(*args, **kwargs)
        self.fields['destination'].queryset = Destination.objects.filter(is_active=True)
