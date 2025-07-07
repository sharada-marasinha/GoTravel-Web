from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('packages/', views.package_list, name='package_list'),
    path('packages/<int:package_id>/', views.package_detail, name='package_detail'),
    path('packages/<int:package_id>/book/', views.book_package, name='book_package'),
    path('packages/<int:package_id>/review/', views.write_review, name='write_review'),
    path('destinations/', views.destinations, name='destinations'),
    path('destinations/<int:destination_id>/', views.destination_detail, name='destination_detail'),
    path('hotels/', views.hotels, name='hotels'),
    path('hotels/<int:hotel_id>/', views.hotel_detail, name='hotel_detail'),
    path('transports/', views.transports, name='transports'),
    path('transports/<int:transport_id>/', views.transport_detail, name='transport_detail'),
    path('bookings/', views.booking_history, name='booking_history'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('profile/', views.profile, name='profile'),
    path('reviews/', views.my_reviews, name='my_reviews'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='travel/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/destinations/', views.destination_suggestions, name='destination_suggestions'),
]
