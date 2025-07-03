from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Destination, Package, Hotel, Transport, Booking, Review, Payment

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'is_active', 'created_at')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'city', 'country')
    ordering = ('name',)

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'package_type', 'price', 'duration_days', 'is_active', 'created_by')
    list_filter = ('package_type', 'is_active', 'destination')
    search_fields = ('name', 'destination__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'star_rating', 'price_per_night', 'is_active')
    list_filter = ('star_rating', 'is_active', 'destination')
    search_fields = ('name', 'destination__name')

@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ('name', 'transport_type', 'from_destination', 'to_destination', 'price', 'is_active')
    list_filter = ('transport_type', 'is_active')
    search_fields = ('name', 'from_destination__name', 'to_destination__name')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'package', 'travel_date', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'package__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'package__name')
    readonly_fields = ('created_at',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'transaction_id', 'is_successful', 'payment_date')
    list_filter = ('is_successful', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'booking__user__username')
    readonly_fields = ('payment_date',)
