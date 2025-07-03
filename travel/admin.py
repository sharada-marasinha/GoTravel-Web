from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
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
    list_display = ('name', 'city', 'country', 'is_active', 'is_popular', 'package_count', 'created_at')
    list_filter = ('country', 'is_active', 'is_popular', 'created_at')
    search_fields = ('name', 'city', 'country')
    ordering = ('name',)
    actions = ['mark_as_popular', 'unmark_as_popular', 'activate_destinations', 'deactivate_destinations']
    
    def package_count(self, obj):
        return obj.package_set.count()
    package_count.short_description = 'Packages'
    
    def mark_as_popular(self, request, queryset):
        updated = queryset.update(is_popular=True)
        self.message_user(request, f'{updated} destinations marked as popular.')
    mark_as_popular.short_description = "Mark selected destinations as popular"
    
    def unmark_as_popular(self, request, queryset):
        updated = queryset.update(is_popular=False)
        self.message_user(request, f'{updated} destinations unmarked as popular.')
    unmark_as_popular.short_description = "Unmark selected destinations as popular"
    
    def activate_destinations(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} destinations activated.')
    activate_destinations.short_description = "Activate selected destinations"
    
    def deactivate_destinations(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} destinations deactivated.')
    deactivate_destinations.short_description = "Deactivate selected destinations"

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'package_type', 'price', 'duration_days', 'is_active', 'is_featured', 'average_rating_display', 'created_by')
    list_filter = ('package_type', 'is_active', 'is_featured', 'destination', 'created_at')
    search_fields = ('name', 'destination__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'average_rating_display')
    actions = ['mark_as_featured', 'unmark_as_featured', 'activate_packages', 'deactivate_packages']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'destination', 'package_type', 'description')
        }),
        ('Pricing & Details', {
            'fields': ('price', 'duration_days', 'max_people')
        }),
        ('Package Content', {
            'fields': ('includes', 'excludes', 'image')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'average_rating_display'),
            'classes': ('collapse',)
        }),
    )
    
    def average_rating_display(self, obj):
        rating = obj.average_rating()
        if rating > 0:
            stars = '★' * int(rating) + '☆' * (5 - int(rating))
            return format_html(f'<span style="color: gold;">{stars}</span> ({rating:.1f})')
        return 'No ratings'
    average_rating_display.short_description = 'Rating'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} packages marked as featured.')
    mark_as_featured.short_description = "Mark selected packages as featured"
    
    def unmark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} packages unmarked as featured.')
    unmark_as_featured.short_description = "Unmark selected packages as featured"
    
    def activate_packages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} packages activated.')
    activate_packages.short_description = "Activate selected packages"
    
    def deactivate_packages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} packages deactivated.')
    deactivate_packages.short_description = "Deactivate selected packages"
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new package
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination', 'star_rating_display', 'price_per_night', 'is_active', 'is_featured', 'created_at')
    list_filter = ('star_rating', 'is_active', 'is_featured', 'destination', 'created_at')
    search_fields = ('name', 'destination__name', 'address')
    actions = ['mark_as_featured', 'unmark_as_featured', 'activate_hotels', 'deactivate_hotels']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'destination', 'address', 'description')
        }),
        ('Hotel Details', {
            'fields': ('star_rating', 'amenities', 'price_per_night', 'image')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    def star_rating_display(self, obj):
        stars = '★' * obj.star_rating + '☆' * (5 - obj.star_rating)
        return format_html(f'<span style="color: gold;">{stars}</span>')
    star_rating_display.short_description = 'Stars'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} hotels marked as featured.')
    mark_as_featured.short_description = "Mark selected hotels as featured"
    
    def unmark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} hotels unmarked as featured.')
    unmark_as_featured.short_description = "Unmark selected hotels as featured"
    
    def activate_hotels(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} hotels activated.')
    activate_hotels.short_description = "Activate selected hotels"
    
    def deactivate_hotels(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} hotels deactivated.')
    deactivate_hotels.short_description = "Deactivate selected hotels"

@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ('name', 'transport_type', 'from_destination', 'to_destination', 'price', 'is_active', 'is_popular', 'created_at')
    list_filter = ('transport_type', 'is_active', 'is_popular', 'created_at')
    search_fields = ('name', 'from_destination__name', 'to_destination__name')
    actions = ['mark_as_popular', 'unmark_as_popular', 'activate_transports', 'deactivate_transports']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'transport_type', 'description')
        }),
        ('Route Details', {
            'fields': ('from_destination', 'to_destination', 'departure_time', 'arrival_time')
        }),
        ('Pricing & Media', {
            'fields': ('price', 'image')
        }),
        ('Status', {
            'fields': ('is_active', 'is_popular')
        }),
    )
    
    def mark_as_popular(self, request, queryset):
        updated = queryset.update(is_popular=True)
        self.message_user(request, f'{updated} transports marked as popular.')
    mark_as_popular.short_description = "Mark selected transports as popular"
    
    def unmark_as_popular(self, request, queryset):
        updated = queryset.update(is_popular=False)
        self.message_user(request, f'{updated} transports unmarked as popular.')
    unmark_as_popular.short_description = "Unmark selected transports as popular"
    
    def activate_transports(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} transports activated.')
    activate_transports.short_description = "Activate selected transports"
    
    def deactivate_transports(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} transports deactivated.')
    deactivate_transports.short_description = "Deactivate selected transports"

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
