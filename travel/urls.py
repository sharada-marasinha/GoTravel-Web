from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('packages/', views.package_list, name='package_list'),
    path('packages/<int:package_id>/', views.package_detail, name='package_detail'),
    path('packages/<int:package_id>/book/', views.book_package, name='book_package'),
    path('packages/<int:package_id>/review/', views.add_review, name='add_review'),
    path('destinations/', views.destinations, name='destinations'),
    path('destinations/<int:destination_id>/', views.destination_detail, name='destination_detail'),
    path('bookings/', views.booking_history, name='booking_history'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='travel/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='travel/logout.html'), name='logout'),
]
