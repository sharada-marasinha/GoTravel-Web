from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Package, Destination, Hotel, Transport, Booking, Review, UserProfile
from .forms import BookingForm, ReviewForm, UserProfileForm, CustomUserCreationForm
import json

def home(request):
    """Home page with featured packages"""
    try:
        featured_packages = Package.objects.filter(is_active=True)[:6]
        destinations = Destination.objects.filter(is_active=True)[:8]
    except:
        featured_packages = []
        destinations = []
    
    # Ensure user profile exists
    if request.user.is_authenticated:
        try:
            UserProfile.objects.get_or_create(user=request.user)
        except:
            pass
    
    template = loader.get_template('travel/home.html')
    context = {
        'featured_packages': featured_packages,
        'destinations': destinations,
    }
    return HttpResponse(template.render(context, request))

def package_list(request):
    """List all packages with search and filter functionality"""
    try:
        packages = Package.objects.filter(is_active=True)
        destinations = Destination.objects.filter(is_active=True)
    except:
        packages = []
        destinations = []
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        packages = packages.filter(
            Q(name__icontains=search_query) |
            Q(destination__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by destination
    destination_id = request.GET.get('destination', '')
    if destination_id:
        try:
            packages = packages.filter(destination_id=int(destination_id))
        except (ValueError, TypeError):
            pass
    
    # Filter by package type
    package_type = request.GET.get('type', '')
    if package_type:
        packages = packages.filter(package_type=package_type)
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        try:
            packages = packages.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            packages = packages.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(packages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    template = loader.get_template('travel/package_list.html')
    context = {
        'page_obj': page_obj,
        'destinations': destinations,
        'search_query': search_query,
        'selected_destination': destination_id,
        'selected_type': package_type,
        'min_price': min_price,
        'max_price': max_price,
    }
    return HttpResponse(template.render(context, request))

def package_detail(request, package_id):
    """Package detail page with booking and reviews"""
    try:
        package = get_object_or_404(Package, id=package_id, is_active=True)
        reviews = Review.objects.filter(package=package).order_by('-created_at')
    except:
        package = None
        reviews = []
    
    template = loader.get_template('travel/package_detail.html')
    context = {
        'package': package,
        'reviews': reviews,
    }
    return HttpResponse(template.render(context, request))

@login_required
def book_package(request, package_id):
    """Book a package"""
    try:
        package = get_object_or_404(Package, id=package_id, is_active=True)
    except:
        messages.error(request, 'Package not found.')
        return redirect('package_list')
    
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
    
    template = loader.get_template('travel/book_package.html')
    context = {
        'package': package,
        'form': form,
    }
    return HttpResponse(template.render(context, request))

@login_required
def booking_detail(request, booking_id):
    """Booking detail page"""
    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    except:
        messages.error(request, 'Booking not found.')
        return redirect('booking_history')
    
    template = loader.get_template('travel/booking_detail.html')
    context = {
        'booking': booking,
    }
    return HttpResponse(template.render(context, request))

@login_required
def booking_history(request):
    """User's booking history"""
    try:
        bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    except:
        bookings = []
    
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    template = loader.get_template('travel/booking_history.html')
    context = {
        'page_obj': page_obj,
    }
    return HttpResponse(template.render(context, request))

def destinations(request):
    """List all destinations"""
    try:
        destinations = Destination.objects.filter(is_active=True)
    except:
        destinations = []
    
    template = loader.get_template('travel/destinations.html')
    context = {
        'destinations': destinations,
    }
    return HttpResponse(template.render(context, request))

def destination_detail(request, destination_id):
    """Destination detail with packages"""
    try:
        destination = get_object_or_404(Destination, id=destination_id, is_active=True)
        packages = Package.objects.filter(destination=destination, is_active=True)
    except:
        destination = None
        packages = []
    
    template = loader.get_template('travel/destination_detail.html')
    context = {
        'destination': destination,
        'packages': packages,
    }
    return HttpResponse(template.render(context, request))

def register(request):
    """User registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            
            # Get or create profile to avoid IntegrityError
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile with form data
            profile.phone = profile_form.cleaned_data.get('phone', '')
            profile.address = profile_form.cleaned_data.get('address', '')
            if profile_form.cleaned_data.get('profile_picture'):
                profile.profile_picture = profile_form.cleaned_data['profile_picture']
            profile.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
        profile_form = UserProfileForm()
    
    template = loader.get_template('travel/register.html')
    context = {
        'form': form,
        'profile_form': profile_form,
    }
    return HttpResponse(template.render(context, request))

@login_required
def profile(request):
    """User profile page"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
    except:
        profile = None
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    template = loader.get_template('travel/profile.html')
    context = {
        'form': form,
        'profile': profile,
    }
    return HttpResponse(template.render(context, request))

@csrf_exempt
def process_payment(request):
    """Process payment for booking"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booking_id = data.get('booking_id')
            
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            
            # Simulate payment processing
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            booking.save()
            
            return JsonResponse({'status': 'success', 'message': 'Payment processed successfully'})
        except:
            return JsonResponse({'status': 'error', 'message': 'Payment processing failed'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def add_review(request, package_id):
    """Add a review for a package"""
    try:
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
        
        template = loader.get_template('travel/add_review.html')
        context = {
            'package': package,
            'form': form,
            'existing_review': existing_review,
        }
        return HttpResponse(template.render(context, request))
    except:
        messages.error(request, 'Package not found.')
        return redirect('package_list')

@login_required
def write_review(request, package_id):
    """Write or update a review for a package"""
    try:
        package = get_object_or_404(Package, id=package_id, is_active=True)
        
        # Check if user has booked this package
        has_booking = Booking.objects.filter(
            user=request.user,
            package=package,
            status__in=['confirmed', 'completed']
        ).exists()
        
        if not has_booking:
            messages.error(request, 'You can only review packages you have booked.')
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
                messages.success(request, 'Review submitted successfully!')
                return redirect('package_detail', package_id=package_id)
        else:
            form = ReviewForm(instance=existing_review)
        
        template = loader.get_template('travel/write_review.html')
        context = {
            'package': package,
            'form': form,
            'existing_review': existing_review,
        }
        return HttpResponse(template.render(context, request))
    except:
        messages.error(request, 'Package not found.')
        return redirect('package_list')

@login_required
def my_reviews(request):
    """Display user's reviews"""
    try:
        reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    except:
        reviews = []
    
    template = loader.get_template('travel/my_reviews.html')
    context = {
        'reviews': reviews,
    }
    return HttpResponse(template.render(context, request))

@login_required
def delete_review(request, review_id):
    """Delete a user's review"""
    try:
        review = get_object_or_404(Review, id=review_id, user=request.user)
        package_id = review.package.id
        review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('package_detail', package_id=package_id)
    except:
        messages.error(request, 'Review not found.')
        return redirect('package_list')

@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
