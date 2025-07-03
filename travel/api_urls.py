from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'packages', api_views.PackageViewSet)
router.register(r'destinations', api_views.DestinationViewSet)
router.register(r'bookings', api_views.BookingViewSet)
router.register(r'reviews', api_views.ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
