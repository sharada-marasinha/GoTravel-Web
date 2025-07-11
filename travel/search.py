"""
Advanced Search Algorithm for Travel Application
This module provides comprehensive search functionality with keyword matching,
fuzzy search, relevance scoring, and intelligent filtering.
"""

import re
from django.db.models import Q, F, Value, IntegerField, Case, When
from django.db.models.functions import Concat, Lower
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from difflib import SequenceMatcher
from .models import Package, Destination, Hotel, Transport
import string


class TravelSearchEngine:
    """Advanced search engine for travel-related content"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 
            'after', 'above', 'below', 'between', 'among', 'within', 'without',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
    def clean_search_query(self, query):
        """Clean and preprocess search query"""
        if not query:
            return []
        
        # Convert to lowercase and remove punctuation
        query = query.lower()
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Split into words and remove stop words
        words = [word.strip() for word in query.split() if word.strip()]
        keywords = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return keywords
    
    def calculate_relevance_score(self, keywords, text_fields):
        """Calculate relevance score based on keyword matches"""
        score = 0
        text_content = ' '.join(str(field) for field in text_fields if field).lower()
        
        for keyword in keywords:
            # Exact match gets highest score
            if keyword in text_content:
                score += 10
            
            # Partial match gets medium score
            if any(keyword in word for word in text_content.split()):
                score += 5
            
            # Fuzzy match gets lower score
            for word in text_content.split():
                if len(word) > 3 and SequenceMatcher(None, keyword, word).ratio() > 0.8:
                    score += 3
        
        return score
    
    def search_packages(self, query, filters=None):
        """Search packages with advanced keyword matching"""
        packages = Package.objects.filter(is_active=True)
        
        if not query:
            return packages
        
        keywords = self.clean_search_query(query)
        if not keywords:
            return packages
        
        # Build Q objects for different search criteria
        search_conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = (
                Q(name__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(includes__icontains=keyword) |
                Q(destination__name__icontains=keyword) |
                Q(destination__city__icontains=keyword) |
                Q(destination__country__icontains=keyword) |
                Q(destination__description__icontains=keyword) |
                Q(package_type__icontains=keyword)
            )
            search_conditions |= keyword_conditions
        
        # Apply search conditions
        packages = packages.filter(search_conditions)
        
        # Add relevance scoring
        packages = packages.annotate(
            relevance_score=Case(
                # Exact name match gets highest score
                When(name__iexact=query, then=Value(100)),
                # Name contains query gets high score
                When(name__icontains=query, then=Value(80)),
                # Destination name match gets medium-high score
                When(destination__name__icontains=query, then=Value(70)),
                # Description match gets medium score
                When(description__icontains=query, then=Value(50)),
                # Other matches get lower scores
                default=Value(30),
                output_field=IntegerField()
            )
        )
        
        # Apply additional filters if provided
        if filters:
            packages = self.apply_filters(packages, filters)
        
        return packages.order_by('-relevance_score', 'name')
    
    def search_destinations(self, query, filters=None):
        """Search destinations with keyword matching"""
        destinations = Destination.objects.filter(is_active=True)
        
        if not query:
            return destinations
        
        keywords = self.clean_search_query(query)
        if not keywords:
            return destinations
        
        search_conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = (
                Q(name__icontains=keyword) |
                Q(city__icontains=keyword) |
                Q(country__icontains=keyword) |
                Q(description__icontains=keyword)
            )
            search_conditions |= keyword_conditions
        
        destinations = destinations.filter(search_conditions)
        
        # Add relevance scoring
        destinations = destinations.annotate(
            relevance_score=Case(
                When(name__iexact=query, then=Value(100)),
                When(name__icontains=query, then=Value(80)),
                When(city__icontains=query, then=Value(70)),
                When(country__icontains=query, then=Value(60)),
                default=Value(40),
                output_field=IntegerField()
            )
        )
        
        return destinations.order_by('-relevance_score', 'name')
    
    def search_hotels(self, query, filters=None):
        """Search hotels with keyword matching"""
        hotels = Hotel.objects.filter(is_active=True)
        
        if not query:
            return hotels
        
        keywords = self.clean_search_query(query)
        if not keywords:
            return hotels
        
        search_conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = (
                Q(name__icontains=keyword) |
                Q(destination__name__icontains=keyword) |
                Q(destination__city__icontains=keyword) |
                Q(destination__country__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(amenities__icontains=keyword) |
                Q(address__icontains=keyword)
            )
            search_conditions |= keyword_conditions
        
        hotels = hotels.filter(search_conditions)
        
        # Add relevance scoring
        hotels = hotels.annotate(
            relevance_score=Case(
                When(name__iexact=query, then=Value(100)),
                When(name__icontains=query, then=Value(80)),
                When(destination__name__icontains=query, then=Value(70)),
                default=Value(50),
                output_field=IntegerField()
            )
        )
        
        if filters:
            hotels = self.apply_hotel_filters(hotels, filters)
        
        return hotels.order_by('-relevance_score', 'name')
    
    def search_transports(self, query, filters=None):
        """Search transports with keyword matching"""
        transports = Transport.objects.filter(is_active=True)
        
        if not query:
            return transports
        
        keywords = self.clean_search_query(query)
        if not keywords:
            return transports
        
        search_conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = (
                Q(name__icontains=keyword) |
                Q(transport_type__icontains=keyword) |
                Q(from_destination__name__icontains=keyword) |
                Q(from_destination__city__icontains=keyword) |
                Q(to_destination__name__icontains=keyword) |
                Q(to_destination__city__icontains=keyword) |
                Q(description__icontains=keyword)
            )
            search_conditions |= keyword_conditions
        
        transports = transports.filter(search_conditions)
        
        # Add relevance scoring
        transports = transports.annotate(
            relevance_score=Case(
                When(name__iexact=query, then=Value(100)),
                When(name__icontains=query, then=Value(80)),
                When(transport_type__icontains=query, then=Value(70)),
                default=Value(50),
                output_field=IntegerField()
            )
        )
        
        if filters:
            transports = self.apply_transport_filters(transports, filters)
        
        return transports.order_by('-relevance_score', 'name')
    
    def unified_search(self, query, search_type='all', filters=None):
        """Unified search across all content types"""
        results = {}
        
        if search_type in ['all', 'packages']:
            results['packages'] = self.search_packages(query, filters)
        
        if search_type in ['all', 'destinations']:
            results['destinations'] = self.search_destinations(query, filters)
        
        if search_type in ['all', 'hotels']:
            results['hotels'] = self.search_hotels(query, filters)
        
        if search_type in ['all', 'transports']:
            results['transports'] = self.search_transports(query, filters)
        
        return results
    
    def search_hotels(self, query, filters=None):
        """Search hotels with advanced keyword matching"""
        if filters is None:
            filters = {}
        
        # Get base queryset
        queryset = Hotel.objects.filter(is_active=True)
        
        # Apply basic filters first
        if filters.get('destination'):
            queryset = queryset.filter(
                Q(destination__name__icontains=filters['destination']) |
                Q(destination__city__icontains=filters['destination']) |
                Q(destination__country__icontains=filters['destination'])
            )
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(price_per_night__gte=float(filters['min_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price_per_night__lte=float(filters['max_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('star_rating'):
            try:
                queryset = queryset.filter(star_rating__gte=int(filters['star_rating']))
            except (ValueError, TypeError):
                pass
        
        # Apply keyword search if query provided
        if query:
            keywords = self.clean_search_query(query)
            if keywords:
                # Create search conditions
                search_conditions = Q()
                
                for keyword in keywords:
                    search_conditions |= (
                        Q(name__icontains=keyword) |
                        Q(description__icontains=keyword) |
                        Q(amenities__icontains=keyword) |
                        Q(destination__name__icontains=keyword) |
                        Q(destination__city__icontains=keyword) |
                        Q(destination__country__icontains=keyword)
                    )
                
                queryset = queryset.filter(search_conditions)
                
                # Calculate relevance scores
                results = []
                for hotel in queryset:
                    relevance_score = self.calculate_relevance_score(
                        keywords, 
                        [hotel.name, hotel.description, hotel.amenities, 
                         hotel.destination.name, hotel.destination.city]
                    )
                    hotel.relevance_score = relevance_score
                    results.append(hotel)
                
                # Sort by relevance
                results.sort(key=lambda x: x.relevance_score, reverse=True)
                
                # Convert back to queryset-like structure
                hotel_ids = [hotel.id for hotel in results]
                queryset = Hotel.objects.filter(id__in=hotel_ids)
                
                # Annotate with relevance scores
                queryset = queryset.annotate(
                    relevance_score=Case(
                        *[When(id=hotel.id, then=Value(hotel.relevance_score)) 
                          for hotel in results],
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-relevance_score')
        
        return queryset
    
    def search_destinations(self, query, filters=None):
        """Search destinations with advanced keyword matching"""
        if filters is None:
            filters = {}
        
        # Get base queryset
        queryset = Destination.objects.filter(is_active=True)
        
        # Apply keyword search if query provided
        if query:
            keywords = self.clean_search_query(query)
            if keywords:
                # Create search conditions
                search_conditions = Q()
                
                for keyword in keywords:
                    search_conditions |= (
                        Q(name__icontains=keyword) |
                        Q(description__icontains=keyword) |
                        Q(city__icontains=keyword) |
                        Q(country__icontains=keyword) |
                        Q(attractions__icontains=keyword)
                    )
                
                queryset = queryset.filter(search_conditions)
                
                # Calculate relevance scores
                results = []
                for destination in queryset:
                    relevance_score = self.calculate_relevance_score(
                        keywords, 
                        [destination.name, destination.description, destination.city, 
                         destination.country, destination.attractions]
                    )
                    destination.relevance_score = relevance_score
                    results.append(destination)
                
                # Sort by relevance
                results.sort(key=lambda x: x.relevance_score, reverse=True)
                
                # Convert back to queryset-like structure
                destination_ids = [dest.id for dest in results]
                queryset = Destination.objects.filter(id__in=destination_ids)
                
                # Annotate with relevance scores
                queryset = queryset.annotate(
                    relevance_score=Case(
                        *[When(id=dest.id, then=Value(dest.relevance_score)) 
                          for dest in results],
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-relevance_score')
        
        return queryset
    
    def search_transports(self, query, filters=None):
        """Search transports with advanced keyword matching"""
        if filters is None:
            filters = {}
        
        # Get base queryset
        queryset = Transport.objects.filter(is_active=True)
        
        # Apply basic filters first
        if filters.get('transport_type'):
            queryset = queryset.filter(transport_type=filters['transport_type'])
        
        if filters.get('from_destination'):
            queryset = queryset.filter(
                Q(from_destination__name__icontains=filters['from_destination']) |
                Q(from_destination__city__icontains=filters['from_destination'])
            )
        
        if filters.get('to_destination'):
            queryset = queryset.filter(
                Q(to_destination__name__icontains=filters['to_destination']) |
                Q(to_destination__city__icontains=filters['to_destination'])
            )
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(price__gte=float(filters['min_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=float(filters['max_price']))
            except (ValueError, TypeError):
                pass
        
        # Apply keyword search if query provided
        if query:
            keywords = self.clean_search_query(query)
            if keywords:
                # Create search conditions
                search_conditions = Q()
                
                for keyword in keywords:
                    search_conditions |= (
                        Q(name__icontains=keyword) |
                        Q(description__icontains=keyword) |
                        Q(transport_type__icontains=keyword) |
                        Q(from_destination__name__icontains=keyword) |
                        Q(to_destination__name__icontains=keyword) |
                        Q(from_destination__city__icontains=keyword) |
                        Q(to_destination__city__icontains=keyword)
                    )
                
                queryset = queryset.filter(search_conditions)
                
                # Calculate relevance scores
                results = []
                for transport in queryset:
                    relevance_score = self.calculate_relevance_score(
                        keywords, 
                        [transport.name, transport.description, transport.transport_type,
                         transport.from_destination.name if transport.from_destination else '',
                         transport.to_destination.name if transport.to_destination else '']
                    )
                    transport.relevance_score = relevance_score
                    results.append(transport)
                
                # Sort by relevance
                results.sort(key=lambda x: x.relevance_score, reverse=True)
                
                # Convert back to queryset-like structure
                transport_ids = [transport.id for transport in results]
                queryset = Transport.objects.filter(id__in=transport_ids)
                
                # Annotate with relevance scores
                queryset = queryset.annotate(
                    relevance_score=Case(
                        *[When(id=transport.id, then=Value(transport.relevance_score)) 
                          for transport in results],
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).order_by('-relevance_score')
        
        return queryset
    
    def search_unified(self, query, filters=None):
        """Unified search across all content types"""
        if filters is None:
            filters = {}
        
        results = {
            'packages': self.search_packages(query, filters),
            'hotels': self.search_hotels(query, filters),
            'destinations': self.search_destinations(query, filters),
            'transports': self.search_transports(query, filters),
        }
        
        return results
    
    def apply_filters(self, queryset, filters):
        """Apply additional filters to package queryset"""
        if filters.get('destination'):
            queryset = queryset.filter(
                Q(destination__name__icontains=filters['destination']) |
                Q(destination__city__icontains=filters['destination']) |
                Q(destination__country__icontains=filters['destination'])
            )
        
        if filters.get('package_type'):
            queryset = queryset.filter(package_type=filters['package_type'])
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(price__gte=float(filters['min_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price__lte=float(filters['max_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('duration_days'):
            try:
                queryset = queryset.filter(duration_days=int(filters['duration_days']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('max_people'):
            try:
                queryset = queryset.filter(max_people__gte=int(filters['max_people']))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def apply_hotel_filters(self, queryset, filters):
        """Apply filters specific to hotels"""
        if filters.get('star_rating'):
            try:
                queryset = queryset.filter(star_rating=int(filters['star_rating']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('min_price'):
            try:
                queryset = queryset.filter(price_per_night__gte=float(filters['min_price']))
            except (ValueError, TypeError):
                pass
        
        if filters.get('max_price'):
            try:
                queryset = queryset.filter(price_per_night__lte=float(filters['max_price']))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def apply_transport_filters(self, queryset, filters):
        """Apply filters specific to transports"""
        if filters.get('transport_type'):
            queryset = queryset.filter(transport_type=filters['transport_type'])
        
        if filters.get('from_destination'):
            queryset = queryset.filter(
                Q(from_destination__name__icontains=filters['from_destination']) |
                Q(from_destination__city__icontains=filters['from_destination'])
            )
        
        if filters.get('to_destination'):
            queryset = queryset.filter(
                Q(to_destination__name__icontains=filters['to_destination']) |
                Q(to_destination__city__icontains=filters['to_destination'])
            )
        
        return queryset
    
    def get_search_suggestions(self, query, limit=10):
        """Get search suggestions based on partial query"""
        if not query or len(query) < 2:
            return []
        
        suggestions = []
        
        # Package suggestions
        packages = Package.objects.filter(
            Q(name__icontains=query) | Q(destinations__name__icontains=query),
            is_active=True
        ).distinct()[:limit//2]
        
        for package in packages:
            # Get the first destination for display (if exists)
            primary_dest = package.destinations.first()
            if primary_dest:
                dest_display = f"{primary_dest.name}, {primary_dest.city}"
            else:
                dest_display = ""
            suggestions.append({
                'text': package.name,
                'type': 'package',
                'destination': dest_display,
                'price': package.price
            })
        
        # Destination suggestions
        destinations = Destination.objects.filter(
            Q(name__icontains=query) | Q(city__icontains=query) | Q(country__icontains=query),
            is_active=True
        )[:limit//2]
        
        for dest in destinations:
            suggestions.append({
                'text': f"{dest.name}, {dest.city}, {dest.country}",
                'type': 'destination',
                'destination': f"{dest.city}, {dest.country}",
                'packages_count': dest.package_set.filter(is_active=True).count()
            })
        
        return suggestions[:limit]
    
    def get_popular_searches(self, limit=10):
        """Get popular search terms based on destination popularity"""
        popular_destinations = Destination.objects.filter(
            is_active=True, 
            is_popular=True
        ).order_by('-created_at')[:limit]
        
        return [
            {
                'text': f"{dest.name}, {dest.city}",
                'type': 'destination',
                'packages_count': dest.package_set.filter(is_active=True).count()
            }
            for dest in popular_destinations
        ]


# Search algorithm utility functions
def fuzzy_match(text1, text2, threshold=0.8):
    """Check if two strings are similar using fuzzy matching"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold


def extract_keywords(text, max_keywords=10):
    """Extract keywords from text content"""
    if not text:
        return []
    
    # Clean text
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # Filter out stop words and short words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 
        'after', 'above', 'below', 'between', 'among', 'within', 'without'
    }
    
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency and return most common
    keyword_freq = {}
    for keyword in keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [keyword for keyword, freq in sorted_keywords[:max_keywords]]


def highlight_search_terms(text, search_terms, max_length=200):
    """Highlight search terms in text and truncate if needed"""
    if not text or not search_terms:
        return text[:max_length] + '...' if len(text) > max_length else text
    
    highlighted = text
    for term in search_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(f'<mark>{term}</mark>', highlighted)
    
    if len(highlighted) > max_length:
        # Find a good breaking point
        break_point = highlighted.rfind(' ', 0, max_length)
        if break_point > max_length - 50:
            highlighted = highlighted[:break_point] + '...'
        else:
            highlighted = highlighted[:max_length] + '...'
    
    return highlighted
