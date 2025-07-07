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
    """Home page with featured packages, popular destinations, featured hotels, and popular transports"""
    try:
        # Get only featured packages - no fallback
        featured_packages = Package.objects.filter(is_active=True, is_featured=True)[:6]
        
        # Get only popular destinations - no fallback
        destinations = Destination.objects.filter(is_active=True, is_popular=True)[:8]
        
        # Get only featured hotels - no fallback
        featured_hotels = Hotel.objects.filter(is_active=True, is_featured=True)[:6]
        
        # Get only popular transports - no fallback
        popular_transports = Transport.objects.filter(is_active=True, is_popular=True)[:6]
        
        # Get all destinations for auto-suggestions
        all_destinations = Destination.objects.filter(is_active=True)
    except:
        featured_packages = []
        destinations = []
        featured_hotels = []
        popular_transports = []
        all_destinations = []
    
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
        'featured_hotels': featured_hotels,
        'popular_transports': popular_transports,
        'all_destinations': all_destinations,
        'today': timezone.now().date(),
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
        # Debug: Check total destinations in database
        total_destinations = Destination.objects.all().count()
        print(f"Total destinations in database: {total_destinations}")
        
        destinations = Destination.objects.filter(is_active=True)
        active_destinations = destinations.count()
        print(f"Active destinations: {active_destinations}")
    except Exception as e:
        print(f"Error fetching destinations: {e}")
        destinations = []
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        destinations = destinations.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(country__icontains=search_query)
        )
        print(f"Destinations after search '{search_query}': {destinations.count()}")
    
    # Filter by country
    country = request.GET.get('country', '')
    if country:
        destinations = destinations.filter(country__icontains=country)
        print(f"Destinations after country filter '{country}': {destinations.count()}")
    
    # Pagination
    paginator = Paginator(destinations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    template = loader.get_template('travel/destinations.html')
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_country': country,
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

def hotels(request):
    """List all hotels with search and filter functionality"""
    try:
        hotels = Hotel.objects.filter(is_active=True)
        destinations = Destination.objects.filter(is_active=True)
    except:
        hotels = []
        destinations = []
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        hotels = hotels.filter(
            Q(name__icontains=search_query) |
            Q(destination__name__icontains=search_query)
        )
    
    # Filter by destination
    destination_id = request.GET.get('destination', '')
    if destination_id:
        try:
            hotels = hotels.filter(destination_id=int(destination_id))
        except (ValueError, TypeError):
            pass
    
    # Filter by star rating
    star_rating = request.GET.get('star_rating', '')
    if star_rating:
        try:
            hotels = hotels.filter(star_rating=int(star_rating))
        except (ValueError, TypeError):
            pass
    
    # Filter by price range
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        try:
            hotels = hotels.filter(price_per_night__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            hotels = hotels.filter(price_per_night__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(hotels, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    template = loader.get_template('travel/hotels.html')
    context = {
        'page_obj': page_obj,
        'destinations': destinations,
        'search_query': search_query,
        'selected_destination': destination_id,
        'selected_star_rating': star_rating,
        'min_price': min_price,
        'max_price': max_price,
    }
    return HttpResponse(template.render(context, request))

def hotel_detail(request, hotel_id):
    """Hotel detail page with packages"""
    try:
        hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
        # Get packages that include this hotel or are in the same destination
        packages = Package.objects.filter(
            destination=hotel.destination, 
            is_active=True,
            package_type__in=['hotel', 'combo']
        )
    except:
        hotel = None
        packages = []
    
    template = loader.get_template('travel/hotel_detail.html')
    context = {
        'hotel': hotel,
        'packages': packages,
    }
    return HttpResponse(template.render(context, request))

def transports(request):
    """List all transports with search and filter functionality"""
    try:
        transports = Transport.objects.filter(is_active=True)
        destinations = Destination.objects.filter(is_active=True)
    except:
        transports = []
        destinations = []
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        transports = transports.filter(
            Q(name__icontains=search_query) |
            Q(from_destination__name__icontains=search_query) |
            Q(to_destination__name__icontains=search_query)
        )
    
    # Filter by transport type
    transport_type = request.GET.get('transport_type', '')
    if transport_type:
        transports = transports.filter(transport_type=transport_type)
    
    # Filter by from destination
    from_destination_id = request.GET.get('from_destination', '')
    if from_destination_id:
        try:
            transports = transports.filter(from_destination_id=int(from_destination_id))
        except (ValueError, TypeError):
            pass
    
    # Filter by to destination
    to_destination_id = request.GET.get('to_destination', '')
    if to_destination_id:
        try:
            transports = transports.filter(to_destination_id=int(to_destination_id))
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(transports, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    template = loader.get_template('travel/transports.html')
    context = {
        'page_obj': page_obj,
        'destinations': destinations,
        'search_query': search_query,
        'selected_transport_type': transport_type,
        'selected_from_destination': from_destination_id,
        'selected_to_destination': to_destination_id,
    }
    return HttpResponse(template.render(context, request))

def transport_detail(request, transport_id):
    """Transport detail page with packages"""
    try:
        transport = get_object_or_404(Transport, id=transport_id, is_active=True)
        # Get packages that include this transport or are in the same destination
        packages = Package.objects.filter(
            Q(destination=transport.from_destination) | Q(destination=transport.to_destination),
            is_active=True,
            package_type__in=['transport', 'combo']
        )
    except:
        transport = None
        packages = []
    
    template = loader.get_template('travel/transport_detail.html')
    context = {
        'transport': transport,
        'packages': packages,
    }
    return HttpResponse(template.render(context, request))

def destination_suggestions(request):
    """API endpoint for destination auto-suggestions"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if len(query) >= 2:  # Start suggesting after 2 characters
        try:
            destinations = Destination.objects.filter(
                Q(name__icontains=query) |
                Q(city__icontains=query) |
                Q(country__icontains=query),
                is_active=True
            ).distinct()[:10]  # Limit to 10 suggestions
            
            for dest in destinations:
                suggestions.append({
                    'id': dest.id,
                    'name': dest.name,
                    'city': dest.city,
                    'country': dest.country,
                    'display': f"{dest.name}, {dest.city}, {dest.country}"
                })
        except:
            pass
    
    return JsonResponse({'suggestions': suggestions})
