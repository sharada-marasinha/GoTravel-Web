from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import UserProfile, Destination, DestinationImage, Package, PackageImage, Hotel, HotelImage, Transport, TransportImage, Booking, Review, Payment

class PackageAdminForm(ModelForm):
    class Meta:
        model = Package
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        hotels = cleaned_data.get('hotels')
        
        # Check if hotels is provided and has at least one hotel
        if not hotels or hotels.count() == 0:
            raise ValidationError({
                'hotels': 'At least one hotel must be selected for this package.'
            })
        
        return cleaned_data

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Image Inline Classes
class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1
    fields = ('image', 'caption', 'is_cover', 'order')
    readonly_fields = ('uploaded_at',)

class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ('image', 'caption', 'is_cover', 'order')
    readonly_fields = ('uploaded_at',)

class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 1
    fields = ('image', 'caption', 'is_cover', 'order')
    readonly_fields = ('uploaded_at',)

class TransportImageInline(admin.TabularInline):
    model = TransportImage
    extra = 1
    fields = ('image', 'caption', 'is_cover', 'order')
    readonly_fields = ('uploaded_at',)

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'is_active', 'is_popular', 'package_count', 'image_count', 'created_at')
    list_filter = ('country', 'is_active', 'is_popular', 'created_at')
    search_fields = ('name', 'city', 'country', 'keywords')
    ordering = ('name',)
    actions = ['mark_as_popular', 'unmark_as_popular', 'activate_destinations', 'deactivate_destinations']
    inlines = [DestinationImageInline]
    
    # Make it easier to add destinations
    fields = ('name', 'city', 'country', 'description', 'keywords', 'image', 'is_active', 'is_popular')
    
    def package_count(self, obj):
        return obj.packages.count()
    package_count.short_description = 'Packages'
    
    def image_count(self, obj):
        count = obj.images.count()
        return format_html(f'<span style="color: #666;">{count} images</span>')
    image_count.short_description = 'Gallery'
    
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

@admin.register(PackageImage)
class PackageImageAdmin(admin.ModelAdmin):
    list_display = ('package', 'image_preview', 'caption', 'is_cover', 'order', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at', 'package')
    search_fields = ('package__name', 'caption')
    ordering = ('package', 'order', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageAdminForm
    list_display = ('name', 'destinations_display', 'package_type', 'price', 'duration_days', 'is_active', 'is_featured', 'average_rating_display', 'image_count', 'hotel_count', 'created_by')
    list_filter = ('package_type', 'is_active', 'is_featured', 'destinations', 'created_at')
    search_fields = ('name', 'destinations__name', 'keywords')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'average_rating_display', 'image_count', 'hotel_count')
    actions = ['mark_as_featured', 'unmark_as_featured', 'activate_packages', 'deactivate_packages']
    inlines = [PackageImageInline]
    filter_horizontal = ('destinations', 'hotels', 'transports')  # Makes it easier to select multiple destinations, hotels, and transports
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'destinations', 'package_type', 'description')
        }),
        ('Included Services', {
            'fields': ('hotels', 'transports'),
            'description': 'Select the hotels and transports included in this package. At least one hotel must be selected.'
        }),
        ('Pricing & Details', {
            'fields': ('price', 'duration_days', 'max_people')
        }),
        ('Package Content', {
            'fields': ('includes', 'excludes', 'keywords', 'image')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'average_rating_display', 'image_count'),
            'classes': ('collapse',)
        }),
    )
    
    def destinations_display(self, obj):
        """Display destinations in a comma-separated format"""
        destinations = obj.destinations.all()
        if destinations:
            destination_names = [dest.name for dest in destinations[:3]]  # Show first 3
            if destinations.count() > 3:
                destination_names.append(f"+ {destinations.count() - 3} more")
            return ", ".join(destination_names)
        return "No destinations"
    destinations_display.short_description = 'Destinations'
    
    def image_count(self, obj):
        count = obj.images.count()
        return format_html(
            '<span style="color: #007cba; font-weight: bold;">{} images</span>',
            count
        )
    image_count.short_description = 'Gallery Images'
    
    def hotel_count(self, obj):
        count = obj.hotels.count()
        color = '#28a745' if count > 0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} hotels</span>',
            color, count
        )
    hotel_count.short_description = 'Included Hotels'
    
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
    list_display = ('name', 'destination', 'star_rating_display', 'price_per_night', 'is_active', 'is_featured', 'image_count', 'created_at')
    list_filter = ('star_rating', 'is_active', 'is_featured', 'destination', 'created_at')
    search_fields = ('name', 'destination__name', 'address', 'keywords')
    actions = ['mark_as_featured', 'unmark_as_featured', 'activate_hotels', 'deactivate_hotels']
    inlines = [HotelImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'destination', 'address', 'description')
        }),
        ('Hotel Details', {
            'fields': ('star_rating', 'amenities', 'price_per_night', 'image')
        }),
        ('Search & Keywords', {
            'fields': ('keywords',),
            'description': 'Add keywords/tags separated by commas for better search functionality'
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    def star_rating_display(self, obj):
        stars = '★' * obj.star_rating + '☆' * (5 - obj.star_rating)
        return format_html(f'<span style="color: gold;">{stars}</span>')
    star_rating_display.short_description = 'Stars'
    
    def image_count(self, obj):
        count = obj.images.count()
        return format_html(f'<span style="color: #666;">{count} images</span>')
    image_count.short_description = 'Gallery'
    
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
    list_display = ('name', 'transport_type', 'from_destination', 'to_destination', 'price', 'is_active', 'is_popular', 'image_count', 'created_at')
    list_filter = ('transport_type', 'is_active', 'is_popular', 'created_at')
    search_fields = ('name', 'from_destination__name', 'to_destination__name', 'keywords')
    actions = ['mark_as_popular', 'unmark_as_popular', 'activate_transports', 'deactivate_transports']
    inlines = [TransportImageInline]
    
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
        ('Search & Keywords', {
            'fields': ('keywords',),
            'description': 'Add keywords/tags separated by commas for better search functionality'
        }),
        ('Status', {
            'fields': ('is_active', 'is_popular')
        }),
    )
    
    def image_count(self, obj):
        count = obj.images.count()
        return format_html(f'<span style="color: #666;">{count} images</span>')
    image_count.short_description = 'Gallery'
    
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

# Individual Image Model Admins
@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'image_preview', 'caption', 'is_cover', 'order', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at', 'hotel')
    search_fields = ('hotel__name', 'caption')
    ordering = ('hotel', 'order', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    list_display = ('destination', 'image_preview', 'caption', 'is_cover', 'order', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at', 'destination')
    search_fields = ('destination__name', 'caption')
    ordering = ('destination', 'order', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(TransportImage)
class TransportImageAdmin(admin.ModelAdmin):
    list_display = ('transport', 'image_preview', 'caption', 'is_cover', 'order', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at', 'transport')
    search_fields = ('transport__name', 'caption')
    ordering = ('transport', 'order', 'uploaded_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'

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
