from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
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
    keywords = models.TextField(blank=True, help_text="Keywords/tags for searching, separated by commas (e.g., beach, mountain, adventure, cultural)")
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular destination")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name}, {self.city}, {self.country}"
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',') if keyword.strip()]
        return []
    
    def get_hotels(self):
        """Get all hotels in this destination"""
        return self.hotel_set.filter(is_active=True)
    
    def get_packages(self):
        """Get all packages for this destination"""
        return self.packages.filter(is_active=True)
    
    def get_transports_from(self):
        """Get all transports departing from this destination"""
        return self.transport_from.filter(is_active=True)
    
    def get_transports_to(self):
        """Get all transports arriving to this destination"""
        return self.transport_to.filter(is_active=True)

class Package(models.Model):
    PACKAGE_TYPES = [
        ('tour', 'Tour Package'),
        ('hotel', 'Hotel Package'),
        ('transport', 'Transport Package'),
        ('combo', 'Combo Package'),
    ]
    
    name = models.CharField(max_length=200)
    destinations = models.ManyToManyField(Destination, related_name='packages', help_text="Destinations included in this package")
    hotels = models.ManyToManyField('Hotel', blank=False, related_name='packages', help_text="Hotels included in this package (At least one hotel must be selected)")
    transports = models.ManyToManyField('Transport', blank=True, related_name='packages', help_text="Transports included in this package")
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    max_people = models.IntegerField()
    includes = models.TextField(help_text="What's included in the package")
    excludes = models.TextField(help_text="What's not included")
    keywords = models.TextField(blank=True, help_text="Keywords/tags for searching, separated by commas (e.g., adventure, luxury, budget, family)")
    image = models.ImageField(upload_to='packages/')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured package")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation to ensure at least one hotel is selected"""
        super().clean()
        # Check if this is an update (instance has primary key)
        if self.pk:
            if not self.hotels.exists():
                raise ValidationError({
                    'hotels': 'At least one hotel must be selected for this package.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called"""
        # For new instances, we can't validate ManyToMany until after save
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # For new instances, validate after save when ManyToMany can be accessed
        if is_new:
            if not self.hotels.exists():
                raise ValidationError('At least one hotel must be selected for this package.')
    
    def average_rating(self):
        reviews = self.review_set.all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',') if keyword.strip()]
        return []
    
    def get_included_hotels(self):
        """Get all hotels included in this package"""
        return self.hotels.filter(is_active=True)
    
    def get_included_transports(self):
        """Get all transports included in this package"""
        return self.transports.filter(is_active=True)
    
    def get_all_destinations(self):
        """Get all destinations included in this package"""
        return self.destinations.filter(is_active=True)
    
    def get_primary_destination(self):
        """Get the first destination (can be used as primary destination)"""
        return self.destinations.filter(is_active=True).first()

class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='packages/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    is_cover = models.BooleanField(default=False, help_text="Use as cover image")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
        verbose_name = "Package Image"
        verbose_name_plural = "Package Images"
    
    def __str__(self):
        return f"{self.package.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # If this is set as cover image, remove cover status from other images
        if self.is_cover:
            PackageImage.objects.filter(package=self.package, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)

class Hotel(models.Model):
    name = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    address = models.TextField()
    star_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    amenities = models.TextField()
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    keywords = models.TextField(blank=True, help_text="Keywords/tags for searching, separated by commas (e.g., luxury, budget, spa, pool, wifi)")
    image = models.ImageField(upload_to='hotels/')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Mark as featured hotel")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_star_display(self):
        return '★' * self.star_rating + '☆' * (5 - self.star_rating)
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',') if keyword.strip()]
        return []
    
    def get_packages(self):
        """Get all packages that include this hotel"""
        return self.packages.filter(is_active=True)
    
    def get_nearby_transports(self):
        """Get transports available from/to this hotel's destination"""
        return Transport.objects.filter(
            models.Q(from_destination=self.destination) | 
            models.Q(to_destination=self.destination),
            is_active=True
        )

class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotels/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    is_cover = models.BooleanField(default=False, help_text="Use as cover image")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
        verbose_name = "Hotel Image"
        verbose_name_plural = "Hotel Images"
    
    def __str__(self):
        return f"{self.hotel.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # If this is set as cover image, remove cover status from other images
        if self.is_cover:
            HotelImage.objects.filter(hotel=self.hotel, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)

class DestinationImage(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='destinations/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    is_cover = models.BooleanField(default=False, help_text="Use as cover image")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
        verbose_name = "Destination Image"
        verbose_name_plural = "Destination Images"
    
    def __str__(self):
        return f"{self.destination.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # If this is set as cover image, remove cover status from other images
        if self.is_cover:
            DestinationImage.objects.filter(destination=self.destination, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)

class Transport(models.Model):
    TRANSPORT_TYPES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('train', 'Train'),
        ('car', 'Car Rental'),
        ('boat', 'Boat'),
        ('taxi', 'Taxi'),
    ]
    
    name = models.CharField(max_length=200)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES)
    from_destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='transport_from')
    to_destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='transport_to')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    keywords = models.TextField(blank=True, help_text="Keywords/tags for searching, separated by commas (e.g., fast, comfortable, budget, luxury)")
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular transport")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='transports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.from_destination} to {self.to_destination}"
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [keyword.strip() for keyword in self.keywords.split(',') if keyword.strip()]
        return []
    
    def get_packages(self):
        """Get all packages that include this transport"""
        return self.packages.filter(is_active=True)
    
    def get_hotels_at_destination(self):
        """Get hotels at the destination of this transport"""
        return Hotel.objects.filter(
            destination__in=[self.from_destination, self.to_destination],
            is_active=True
        )
    
    def duration(self):
        """Calculate journey duration"""
        from datetime import datetime, timedelta
        
        # Handle overnight journeys
        departure = datetime.combine(datetime.today(), self.departure_time)
        arrival = datetime.combine(datetime.today(), self.arrival_time)
        
        if arrival < departure:
            arrival += timedelta(days=1)
        
        duration = arrival - departure
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if duration.days > 0:
            return f"{duration.days}d {hours}h {minutes}m"
        else:
            return f"{hours}h {minutes}m"

class TransportImage(models.Model):
    transport = models.ForeignKey(Transport, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='transports/gallery/')
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption for the image")
    is_cover = models.BooleanField(default=False, help_text="Use as cover image")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers first)")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
        verbose_name = "Transport Image"
        verbose_name_plural = "Transport Images"
    
    def __str__(self):
        return f"{self.transport.name} - Image {self.id}"
    
    def save(self, *args, **kwargs):
        # If this is set as cover image, remove cover status from other images
        if self.is_cover:
            TransportImage.objects.filter(transport=self.transport, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)

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
