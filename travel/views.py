from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Package, Destination, Hotel, Transport, Booking, Review, UserProfile
from .forms import BookingForm, ReviewForm, UserProfileForm
import json

def home(request):
    """Home page with featured packages"""
    featured_packages = Package.objects.filter(is_active=True)[:6]
    destinations = Destination.objects.filter(is_active=True)[:8]
    context = {
        'featured_packages': featured_packages,
        'destinations': destinations,
    }
    return render(request, 'travel/home.html', context)

def package_list(request):
    """List all packages with search and filter functionality"""
    packages = Package.objects.filter(is_active=True)
    destinations = Destination.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        packages = packages.filter(
            Q(name__icontains=search_query) |
            Q(destination__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by destination
    destination_id = request.GET.get('destination')
    if destination_id:
        packages = packages.filter(destination_id=destination_id)
    
    # Filter by package type
    package_type = request.GET.get('type')
    if package_type:
        packages = packages.filter(package_type=package_type)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        packages = packages.filter(price__gte=min_price)
    if max_price:
        packages = packages.filter(price__lte=max_price)
    
    # Pagination
    paginator = Paginator(packages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'destinations': destinations,
        'search_query': search_query,
        'selected_destination': destination_id,
        'selected_type': package_type,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'travel/package_list.html', context)

def package_detail(request, package_id):
    """Package detail page with booking and reviews"""
    package = get_object_or_404(Package, id=package_id, is_active=True)
    reviews = Review.objects.filter(package=package).order_by('-created_at')
    
    context = {
        'package': package,
        'reviews': reviews,
    }
    return render(request, 'travel/package_detail.html', context)

@login_required
def book_package(request, package_id):
    """Book a package"""
    package = get_object_or_404(Package, id=package_id, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.package = package
            booking.total_amount = package.price * booking.num_people
            booking.save()
            messages.success(request, 'Booking created successfully!')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = BookingForm()
    
    context = {
        'package': package,
        'form': form,
    }
    return render(request, 'travel/book_package.html', context)

@login_required
def booking_detail(request, booking_id):
    """Booking detail page"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {
        'booking': booking,
    }
    return render(request, 'travel/booking_detail.html', context)

@login_required
def booking_history(request):
    """User's booking history"""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'travel/booking_history.html', context)

@login_required
def add_review(request, package_id):
    """Add a review for a package"""
    package = get_object_or_404(Package, id=package_id)
    
    # Check if user has booked this package
    has_booking = Booking.objects.filter(
        user=request.user,
        package=package,
        status='completed'
    ).exists()
    
    if not has_booking:
        messages.error(request, 'You can only review packages you have booked and completed.')
        return redirect('package_detail', package_id=package_id)
    
    # Check if user has already reviewed this package
    existing_review = Review.objects.filter(user=request.user, package=package).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.package = package
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('package_detail', package_id=package_id)
    else:
        form = ReviewForm(instance=existing_review)
    
    context = {
        'package': package,
        'form': form,
        'existing_review': existing_review,
    }
    return render(request, 'travel/add_review.html', context)

def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
        profile_form = UserProfileForm()
    
    context = {
        'form': form,
        'profile_form': profile_form,
    }
    return render(request, 'travel/register.html', context)

@login_required
def profile(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'travel/profile.html', context)

@csrf_exempt
def process_payment(request):
    """Process payment for booking"""
    if request.method == 'POST':
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        # Simulate payment processing
        # In a real application, integrate with payment gateway
        booking.payment_status = 'paid'
        booking.status = 'confirmed'
        booking.save()
        
        return JsonResponse({'status': 'success', 'message': 'Payment processed successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def destinations(request):
    """List all destinations"""
    destinations = Destination.objects.filter(is_active=True)
    context = {
        'destinations': destinations,
    }
    return render(request, 'travel/destinations.html', context)

def destination_detail(request, destination_id):
    """Destination detail with packages"""
    destination = get_object_or_404(Destination, id=destination_id, is_active=True)
    packages = Package.objects.filter(destination=destination, is_active=True)
    
    context = {
        'destination': destination,
        'packages': packages,
    }
    return render(request, 'travel/destination_detail.html', context)
