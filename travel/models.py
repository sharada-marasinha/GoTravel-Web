from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class UserProfile(models.Model):
    USER_ROLES = [
        ('admin', 'Admin'),
        ('agent', 'Agent'),
        ('customer', 'Customer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class Destination(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='destinations/')
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular destination")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name}, {self.city}, {self.country}"

class Package(models.Model):
    PACKAGE_TYPES = [
        ('tour', 'Tour Package'),
        ('hotel', 'Hotel Package'),
        ('transport', 'Transport Package'),
        ('combo', 'Combo Package'),
    ]
    
    name = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    max_people = models.IntegerField()
    includes = models.TextField(help_text="What's included in the package")
    excludes = models.TextField(help_text="What's not included")
    image = models.ImageField(upload_to='packages/')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured package")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def average_rating(self):
        reviews = self.review_set.all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0

class Hotel(models.Model):
    name = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    address = models.TextField()
    star_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    amenities = models.TextField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='hotels/')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured hotel")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_star_display(self):
        return '★' * self.star_rating + '☆' * (5 - self.star_rating)

class Transport(models.Model):
    TRANSPORT_TYPES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('car', 'Car Rental'),
    ]
    
    name = models.CharField(max_length=200)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES)
    from_destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='transport_from')
    to_destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='transport_to')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular transport")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='transports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.from_destination} to {self.to_destination}"

class Booking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    transport = models.ForeignKey(Transport, on_delete=models.CASCADE, null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    num_people = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.username}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'package']
    
    def __str__(self):
        return f"{self.user.username} - {self.package.name} - {self.rating} stars"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment #{self.transaction_id} - {self.amount}"
