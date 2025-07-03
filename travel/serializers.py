from rest_framework import serializers
from .models import Package, Destination, Booking, Review, Hotel, Transport

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'country', 'city', 'description', 'image']

class PackageSerializer(serializers.ModelSerializer):
    destination = DestinationSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Package
        fields = ['id', 'name', 'destination', 'package_type', 'description', 'price', 
                 'duration_days', 'max_people', 'includes', 'excludes', 'image', 'average_rating']

class BookingSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    package_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'package', 'package_id', 'travel_date', 'return_date', 'num_people', 
                 'total_amount', 'status', 'payment_status', 'special_requests', 'created_at']
        read_only_fields = ['total_amount', 'status', 'payment_status']

class ReviewSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    package_id = serializers.IntegerField(write_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'package', 'package_id', 'user_name', 'rating', 'comment', 'created_at']
