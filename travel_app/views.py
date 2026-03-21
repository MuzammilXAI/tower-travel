from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from .models import Destination, Flight, Hotel, Package, Review, Booking, Contact, NewsletterSubscriber
import random
import re
from django.core.mail import send_mail
import string
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import timedelta
import json
from django.conf import settings  # Add this line
from decimal import Decimal
from django.http import JsonResponse
from django.db.models import Q

def generate_ticket_number():
    """Generate unique ticket number"""
    return 'TKT-' + ''.join(random.choices(string.digits, k=8))


# --- USER AUTH VIEWS ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            return redirect('reset_password', username=username)
        except User.DoesNotExist:
            messages.error(request, 'Username not found.')
            return redirect('forgot_password')
    return render(request, 'forgot_password.html')


def reset_password_view(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successfully! Please login with your new password.')
            return redirect('login')

    return render(request, 'reset_password.html', {'username': username})


# --- MODULE VIEWS ---
@login_required(login_url='login')
def index_view(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def destination_view(request):
    from datetime import date
    today = date.today()

    destinations = Destination.objects.filter(is_active=True)

    # Filter by search
    search_query = request.GET.get('search', '')
    if search_query:
        destinations = destinations.filter(
            Q(name__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        destinations = destinations.filter(category=category)

    # Filter by budget
    budget = request.GET.get('budget', '')
    if budget:
        destinations = destinations.filter(budget=budget)

    context = {
        'destinations': destinations,
        'today': today,  # ADD THIS LINE
        'search_query': search_query,
        'selected_category': category,
        'selected_budget': budget,
    }
    return render(request, 'destination.html', context)



@login_required(login_url='login')
def flight_view(request):
    flights = Flight.objects.filter(is_active=True)

    # Filter by from city
    from_city = request.GET.get('from', '')
    if from_city:
        flights = flights.filter(from_city__icontains=from_city)

    # Filter by to city
    to_city = request.GET.get('to', '')
    if to_city:
        flights = flights.filter(to_city__icontains=to_city)

    # Filter by date
    date = request.GET.get('date', '')
    if date:
        flights = flights.filter(departure_date=date)

    # Filter by price category
    price = request.GET.get('price', '')
    if price:
        flights = flights.filter(price_category=price)

    context = {
        'flights': flights,
        'from_city': from_city,
        'to_city': to_city,
        'selected_date': date,
        'selected_price': price,
    }
    return render(request, 'flight.html', context)


@login_required(login_url='login')
def hotel_view(request):
    hotels = Hotel.objects.all()

    # Filter by search
    search_query = request.GET.get('search', '')
    if search_query:
        hotels = hotels.filter(name__icontains=search_query)

    # Filter by location
    location = request.GET.get('location', '')
    if location:
        hotels = hotels.filter(location=location)

    # Filter by price
    price = request.GET.get('price', '')
    if price:
        hotels = hotels.filter(price_category=price)

    # Filter by rating
    rating = request.GET.get('rating', '')
    if rating:
        hotels = hotels.filter(rating__gte=int(rating))

    context = {
        'hotels': hotels,
        'search_query': search_query,
        'selected_location': location,
        'selected_price': price,
        'selected_rating': rating,
    }
    return render(request, 'hotel.html', context)


@login_required(login_url='login')
def package_view(request):
    packages = Package.objects.filter(is_active=True)
    context = {'packages': packages}
    return render(request, 'package.html', context)


@login_required(login_url='login')
def reviews_view(request):
    if request.method == 'POST':
        review_type = request.POST.get('review_type')
        name = request.POST.get('name')
        text = request.POST.get('text')
        rating = request.POST.get('rating')

        if name and text and rating:
            # Create review without is_approved field
            review = Review(
                user=request.user if request.user.is_authenticated else None,
                review_type=review_type,
                name=name,
                text=text,
                rating=int(rating),
            )
            # Try to set is_approved if the field exists
            try:
                review.is_approved = False
            except:
                pass
            review.save()
            messages.success(request, 'Review submitted successfully! It will be visible after approval.')
        else:
            messages.error(request, 'Please fill all fields.')
        return redirect('reviews')

    # Safely get reviews
    try:
        # Try to filter by is_approved
        reviews = Review.objects.filter(is_approved=True).order_by('-created_at')
    except:
        # If column doesn't exist, show all reviews
        reviews = Review.objects.all().order_by('-created_at')

    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
    }
    return render(request, 'reviews.html', context)


# --- ENHANCED BOOKING VIEWS ---
@login_required(login_url='login')
def book_item(request):
    """Enhanced booking function for all item types with payment fields"""
    if request.method == 'POST':
        try:
            # Get common booking data
            booking_type = request.POST.get('booking_type')
            item_id = request.POST.get('item_id')
            travel_date = request.POST.get('travel_date')
            people = int(request.POST.get('people', 1))

            # Get contact information
            full_name = request.POST.get('full_name', request.user.get_full_name() or request.user.username)
            email = request.POST.get('email', request.user.email)
            phone = request.POST.get('phone', '')
            special_requests = request.POST.get('special_requests', '')

            # Initialize variables
            item_name = ""
            price_per_unit = 0
            item_details = ""
            return_date = None
            number_of_rooms = 1

            # Get details based on booking type
            if booking_type == 'destination':
                destination = get_object_or_404(Destination, id=item_id)
                item_name = destination.name
                price_per_unit = float(destination.price_per_day)
                item_details = f"Destination: {destination.name}, Country: {destination.country}, Category: {destination.category}"

            elif booking_type == 'hotel':
                hotel = get_object_or_404(Hotel, id=item_id)
                item_name = hotel.name
                price_per_unit = float(hotel.price_per_night)
                number_of_rooms = int(request.POST.get('rooms', 1))
                check_in = travel_date
                check_out = request.POST.get('check_out_date')
                if check_out:
                    return_date = check_out
                item_details = f"Hotel: {hotel.name}, Location: {hotel.location}, Rating: {hotel.rating}★"

                # Update hotel availability
                if hotel.available_rooms >= number_of_rooms:
                    hotel.available_rooms -= number_of_rooms
                    hotel.save()
                else:
                    messages.error(request, 'Not enough rooms available')
                    return redirect(request.META.get('HTTP_REFERER', 'index'))

            elif booking_type == 'flight':
                flight = get_object_or_404(Flight, id=item_id)
                item_name = f"{flight.get_airline_display()} {flight.flight_number}"
                price_per_unit = float(flight.price)
                item_details = f"Flight: {flight.get_airline_display()} {flight.flight_number}, From: {flight.from_city} To: {flight.to_city}, Departure: {flight.departure_time}"

                # Update flight seats
                if flight.available_seats >= people:
                    flight.available_seats -= people
                    flight.save()
                else:
                    messages.error(request, 'Not enough seats available')
                    return redirect(request.META.get('HTTP_REFERER', 'index'))

            elif booking_type == 'package':
                package = get_object_or_404(Package, id=item_id)
                item_name = package.name
                price_per_unit = float(package.discounted_price)
                item_details = f"Package: {package.name}, Duration: {package.duration_days} days, Includes: {package.includes}"

            # Calculate total price
            if booking_type == 'hotel':
                # Calculate number of nights for hotel
                from datetime import datetime
                check_in_date = datetime.strptime(travel_date, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(return_date, '%Y-%m-%d').date() if return_date else check_in_date
                nights = (check_out_date - check_in_date).days
                if nights <= 0:
                    nights = 1
                total_price = price_per_unit * number_of_rooms * nights
            else:
                total_price = price_per_unit * people

            # Generate unique ticket number
            ticket_number = generate_ticket_number()

            # Create booking with payment fields
            booking = Booking.objects.create(
                user=request.user,
                booking_type=booking_type,
                item_id=item_id,
                item_name=item_name,
                item_details=item_details,
                travel_date=travel_date,
                return_date=return_date,
                number_of_people=people,
                number_of_rooms=number_of_rooms if booking_type == 'hotel' else 1,
                price_per_unit=price_per_unit,
                total_price=total_price,
                full_name=full_name,
                email=email,
                phone=phone,
                special_requests=special_requests,
                ticket_number=ticket_number,
                status='confirmed',  # Booking confirmed even without payment

                # PAYMENT FIELDS
                payment_status='pending',
                amount_paid=0,
                remaining_amount=total_price,
                payment_due_date=timezone.now().date() + timedelta(days=7)  # Due in 7 days
            )

            messages.success(request, f'✅ Booking confirmed! Your ticket number is {ticket_number}')
            messages.info(request, '⚠️ Payment is pending. Please complete payment within 7 days.')

            # Store booking info in session for receipt
            request.session['last_booking'] = {
                'ticket_number': ticket_number,
                'item_name': item_name,
                'total_price': float(total_price),
                'booking_type': booking_type,
                'booking_id': booking.id
            }

            return redirect('booking_confirmation')

        except Exception as e:
            messages.error(request, f'Booking failed: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'index'))

    return redirect('index')


@login_required(login_url='login')
def cancel_booking(request):
    """Cancel a booking"""
    if request.method == 'POST':
        booking_type = request.POST.get('booking_type')
        item_name = request.POST.get('item_name')
        booking_id = request.POST.get('booking_id')

        # Find and cancel the booking
        booking = Booking.objects.filter(
            user=request.user,
            id=booking_id,
            status='confirmed'
        ).first()

        if booking:
            # Restore availability
            if booking.booking_type == 'hotel':
                hotel = Hotel.objects.filter(id=booking.item_id).first()
                if hotel:
                    hotel.available_rooms += booking.number_of_rooms
                    hotel.save()
            elif booking.booking_type == 'flight':
                flight = Flight.objects.filter(id=booking.item_id).first()
                if flight:
                    flight.available_seats += booking.number_of_people
                    flight.save()

            booking.status = 'cancelled'
            booking.save()
            messages.success(request, f'Booking for {item_name} has been cancelled.')
        else:
            messages.error(request, 'No active booking found.')

        return redirect('my_bookings')

    return redirect('index')


@login_required(login_url='login')
def my_bookings(request):
    """View user's bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    context = {
        'bookings': bookings,
        'active_bookings': bookings.filter(status='confirmed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
    }
    return render(request, 'my_bookings.html', context)


@login_required(login_url='login')
def booking_confirmation(request):
    """Booking confirmation page"""
    last_booking = request.session.get('last_booking')
    if not last_booking:
        return redirect('index')

    booking = Booking.objects.filter(ticket_number=last_booking['ticket_number']).first()
    context = {
        'booking': booking,
        'ticket_number': last_booking['ticket_number'],
        'item_name': last_booking['item_name'],
        'total_price': last_booking['total_price'],
        'payment_due_date': booking.payment_due_date if booking else None,
        'payment_status': booking.payment_status if booking else 'pending'
    }
    return render(request, 'booking_confirmation.html', context)
# ==================== ADMIN PANEL VIEWS ====================
@staff_member_required(login_url='login')
def admin_page_view(request):
    """Main admin dashboard view with complete statistics"""

    # Get date ranges for filters
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # ===== USER STATISTICS =====
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    new_users_month = User.objects.filter(date_joined__date__gte=month_ago).count()

    # ===== DESTINATION STATISTICS =====
    total_destinations = Destination.objects.count()
    active_destinations = Destination.objects.filter(is_active=True).count()
    inactive_destinations = Destination.objects.filter(is_active=False).count()

    # Destinations by category
    destinations_by_category = Destination.objects.values('category').annotate(
        count=Count('id')
    ).order_by('category')

    # Destinations by budget
    destinations_by_budget = Destination.objects.values('budget').annotate(
        count=Count('id')
    ).order_by('budget')

    # Popular destinations (most booked)
    popular_destinations = Booking.objects.filter(booking_type='destination') \
        .values('item_name') \
        .annotate(bookings=Count('id')) \
        .order_by('-bookings')[:5]

    # ===== HOTEL STATISTICS =====
    total_hotels = Hotel.objects.count()
    available_hotels = Hotel.objects.filter(available_rooms__gt=0).count()
    fully_booked_hotels = Hotel.objects.filter(available_rooms=0).count()

    # Hotels by location
    hotels_by_location = Hotel.objects.values('location').annotate(
        count=Count('id')
    ).order_by('location')

    # Hotels by rating
    hotels_by_rating = Hotel.objects.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')

    # Hotels by price category
    hotels_by_price = Hotel.objects.values('price_category').annotate(
        count=Count('id')
    ).order_by('price_category')

    # Total rooms available across all hotels
    total_rooms_available = Hotel.objects.aggregate(Sum('available_rooms'))['available_rooms__sum'] or 0

    # Popular hotels (most booked)
    popular_hotels = Booking.objects.filter(booking_type='hotel') \
        .values('item_name') \
        .annotate(bookings=Count('id')) \
        .order_by('-bookings')[:5]

    # ===== FLIGHT STATISTICS =====
    total_flights = Flight.objects.count()
    active_flights = Flight.objects.filter(is_active=True).count()
    inactive_flights = Flight.objects.filter(is_active=False).count()

    # Upcoming flights (next 7 days)
    upcoming_flights = Flight.objects.filter(
        departure_date__gte=today,
        departure_date__lte=today + timedelta(days=7),
        is_active=True
    ).count()

    # Flights by airline
    flights_by_airline = Flight.objects.values('airline').annotate(
        count=Count('id')
    ).order_by('airline')

    # Flights by price category
    flights_by_price = Flight.objects.values('price_category').annotate(
        count=Count('id')
    ).order_by('price_category')

    # Total seats available
    total_seats_available = Flight.objects.aggregate(Sum('available_seats'))['available_seats__sum'] or 0

    # Popular flights (most booked)
    popular_flights = Booking.objects.filter(booking_type='flight') \
        .values('item_name') \
        .annotate(bookings=Count('id')) \
        .order_by('-bookings')[:5]

    # ===== PACKAGE STATISTICS =====
    total_packages = Package.objects.count()
    active_packages = Package.objects.filter(is_active=True).count()
    inactive_packages = Package.objects.filter(is_active=False).count()

    # Packages with discounts
    packages_with_discount = Package.objects.filter(discount_percentage__gt=0).count()

    # Average package price
    avg_package_price = Package.objects.aggregate(Avg('price_per_person'))['price_per_person__avg'] or 0

    # Packages by duration
    short_packages = Package.objects.filter(duration_days__lte=3).count()
    medium_packages = Package.objects.filter(duration_days__gte=4, duration_days__lte=7).count()
    long_packages = Package.objects.filter(duration_days__gt=7).count()

    # Popular packages (most booked)
    popular_packages = Booking.objects.filter(booking_type='package') \
        .values('item_name') \
        .annotate(bookings=Count('id')) \
        .order_by('-bookings')[:5]

    # ===== BOOKING STATISTICS =====
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    pending_bookings = Booking.objects.filter(status='pending').count()

    # Bookings by type
    destination_bookings = Booking.objects.filter(booking_type='destination').count()
    hotel_bookings = Booking.objects.filter(booking_type='hotel').count()
    flight_bookings = Booking.objects.filter(booking_type='flight').count()
    package_bookings = Booking.objects.filter(booking_type='package').count()

    # Today's bookings
    bookings_today = Booking.objects.filter(booking_date__date=today).count()
    bookings_week = Booking.objects.filter(booking_date__date__gte=week_ago).count()
    bookings_month = Booking.objects.filter(booking_date__date__gte=month_ago).count()

    # ===== REVENUE STATISTICS =====
    total_revenue = Booking.objects.filter(status='confirmed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_today = Booking.objects.filter(
        status='confirmed',
        booking_date__date=today
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_week = Booking.objects.filter(
        status='confirmed',
        booking_date__date__gte=week_ago
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_month = Booking.objects.filter(
        status='confirmed',
        booking_date__date__gte=month_ago
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # ===== REVIEW STATISTICS =====
    total_reviews = Review.objects.count()
    approved_reviews = Review.objects.filter(is_approved=True).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    avg_rating = Review.objects.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0

    # Reviews by rating
    reviews_by_rating = Review.objects.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')

    # ===== CONTACT STATISTICS =====
    total_contacts = Contact.objects.count()
    resolved_contacts = Contact.objects.filter(is_resolved=True).count()
    unresolved_contacts = Contact.objects.filter(is_resolved=False).count()

    # ===== NEWSLETTER STATISTICS =====
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    inactive_subscribers = NewsletterSubscriber.objects.filter(is_active=False).count()

    # ===== RECENT ACTIVITY =====
    recent_bookings = Booking.objects.select_related('user').order_by('-booking_date')[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    recent_reviews = Review.objects.all().order_by('-created_at')[:10]
    recent_contacts = Contact.objects.all().order_by('-created_at')[:10]

    # ===== ALL DATA FOR TABLES =====
    all_users = User.objects.all().order_by('-date_joined')
    all_destinations = Destination.objects.all()
    all_hotels = Hotel.objects.all()
    all_flights = Flight.objects.all().order_by('departure_date')
    all_packages = Package.objects.all()
    all_bookings = Booking.objects.select_related('user').order_by('-booking_date')
    all_reviews = Review.objects.all().order_by('-created_at')
    all_contacts = Contact.objects.all().order_by('-created_at')
    all_subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')

    context = {
        # User Statistics
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'all_users': all_users,

        # Destination Statistics
        'total_destinations': total_destinations,
        'active_destinations': active_destinations,
        'inactive_destinations': inactive_destinations,
        'destinations_by_category': destinations_by_category,
        'destinations_by_budget': destinations_by_budget,
        'popular_destinations': popular_destinations,
        'all_destinations': all_destinations,

        # Hotel Statistics
        'total_hotels': total_hotels,
        'available_hotels': available_hotels,
        'fully_booked_hotels': fully_booked_hotels,
        'hotels_by_location': hotels_by_location,
        'hotels_by_rating': hotels_by_rating,
        'hotels_by_price': hotels_by_price,
        'total_rooms_available': total_rooms_available,
        'popular_hotels': popular_hotels,
        'all_hotels': all_hotels,

        # Flight Statistics
        'total_flights': total_flights,
        'active_flights': active_flights,
        'inactive_flights': inactive_flights,
        'upcoming_flights': upcoming_flights,
        'flights_by_airline': flights_by_airline,
        'flights_by_price': flights_by_price,
        'total_seats_available': total_seats_available,
        'popular_flights': popular_flights,
        'all_flights': all_flights,

        # Package Statistics
        'total_packages': total_packages,
        'active_packages': active_packages,
        'inactive_packages': inactive_packages,
        'packages_with_discount': packages_with_discount,
        'avg_package_price': avg_package_price,
        'short_packages': short_packages,
        'medium_packages': medium_packages,
        'long_packages': long_packages,
        'popular_packages': popular_packages,
        'all_packages': all_packages,

        # Booking Statistics
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'pending_bookings': pending_bookings,
        'destination_bookings': destination_bookings,
        'hotel_bookings': hotel_bookings,
        'flight_bookings': flight_bookings,
        'package_bookings': package_bookings,
        'bookings_today': bookings_today,
        'bookings_week': bookings_week,
        'bookings_month': bookings_month,
        'all_bookings': all_bookings,

        # Revenue Statistics
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,

        # Review Statistics
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'avg_rating': avg_rating,
        'reviews_by_rating': reviews_by_rating,
        'all_reviews': all_reviews,

        # Contact Statistics
        'total_contacts': total_contacts,
        'resolved_contacts': resolved_contacts,
        'unresolved_contacts': unresolved_contacts,
        'all_contacts': all_contacts,

        # Newsletter Statistics
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'inactive_subscribers': inactive_subscribers,
        'all_subscribers': all_subscribers,

        # Recent Activity
        'recent_bookings': recent_bookings,
        'recent_users': recent_users,
        'recent_reviews': recent_reviews,
        'recent_contacts': recent_contacts,
    }

    return render(request, 'admin.html', context)



# ===== USER MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password != confirm:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f'User {username} created successfully')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            messages.error(request, 'Cannot delete superuser')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully')
    except User.DoesNotExist:
        messages.error(request, 'User not found')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_activate_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} activated successfully')
    except User.DoesNotExist:
        messages.error(request, 'User not found')
    return redirect('admin_page')


# ===== DESTINATION MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_add_destination(request):
    if request.method == 'POST':
        Destination.objects.create(
            name=request.POST.get('name'),
            country=request.POST.get('country'),
            category=request.POST.get('category'),
            budget=request.POST.get('budget'),
            description=request.POST.get('description'),
            image_url=request.POST.get('image_url'),
            price_per_day=request.POST.get('price_per_day'),
            is_active=True
        )
        messages.success(request, 'Destination added successfully')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_edit_destination(request, dest_id):
    destination = get_object_or_404(Destination, id=dest_id)
    if request.method == 'POST':
        destination.name = request.POST.get('name')
        destination.country = request.POST.get('country')
        destination.category = request.POST.get('category')
        destination.budget = request.POST.get('budget')
        destination.description = request.POST.get('description')
        destination.image_url = request.POST.get('image_url')
        destination.price_per_day = request.POST.get('price_per_day')
        destination.is_active = request.POST.get('is_active') == 'on'
        destination.save()
        messages.success(request, 'Destination updated successfully')
        return redirect('admin_page')

    return render(request, 'edit_destination.html', {'destination': destination})


@staff_member_required(login_url='login')
def admin_delete_destination(request, dest_id):
    try:
        dest = Destination.objects.get(id=dest_id)
        dest.delete()
        messages.success(request, 'Destination deleted successfully')
    except Destination.DoesNotExist:
        messages.error(request, 'Destination not found')
    return redirect('admin_page')


# ===== HOTEL MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_add_hotel(request):
    if request.method == 'POST':
        Hotel.objects.create(
            name=request.POST.get('name'),
            location=request.POST.get('location'),
            price_category=request.POST.get('price_category'),
            rating=request.POST.get('rating'),
            description=request.POST.get('description'),
            image_url=request.POST.get('image_url'),
            price_per_night=request.POST.get('price_per_night'),
            available_rooms=request.POST.get('available_rooms'),
            amenities=request.POST.get('amenities')
        )
        messages.success(request, 'Hotel added successfully')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_edit_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        hotel.name = request.POST.get('name')
        hotel.location = request.POST.get('location')
        hotel.price_category = request.POST.get('price_category')
        hotel.rating = request.POST.get('rating')
        hotel.description = request.POST.get('description')
        hotel.image_url = request.POST.get('image_url')
        hotel.price_per_night = request.POST.get('price_per_night')
        hotel.available_rooms = request.POST.get('available_rooms')
        hotel.amenities = request.POST.get('amenities')
        hotel.save()
        messages.success(request, 'Hotel updated successfully')
        return redirect('admin_page')

    return render(request, 'edit_hotel.html', {'hotel': hotel})


@staff_member_required(login_url='login')
def admin_delete_hotel(request, hotel_id):
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        hotel.delete()
        messages.success(request, 'Hotel deleted successfully')
    except Hotel.DoesNotExist:
        messages.error(request, 'Hotel not found')
    return redirect('admin_page')


# ===== FLIGHT MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_add_flight(request):
    if request.method == 'POST':
        Flight.objects.create(
            airline=request.POST.get('airline'),
            flight_number=request.POST.get('flight_number'),
            from_city=request.POST.get('from_city'),
            to_city=request.POST.get('to_city'),
            departure_date=request.POST.get('departure_date'),
            departure_time=request.POST.get('departure_time'),
            arrival_time=request.POST.get('arrival_time'),
            duration=request.POST.get('duration'),
            price=request.POST.get('price'),
            price_category=request.POST.get('price_category'),
            available_seats=request.POST.get('available_seats'),
            is_active=True
        )
        messages.success(request, 'Flight added successfully')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_edit_flight(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    if request.method == 'POST':
        flight.airline = request.POST.get('airline')
        flight.flight_number = request.POST.get('flight_number')
        flight.from_city = request.POST.get('from_city')
        flight.to_city = request.POST.get('to_city')
        flight.departure_date = request.POST.get('departure_date')
        flight.departure_time = request.POST.get('departure_time')
        flight.arrival_time = request.POST.get('arrival_time')
        flight.duration = request.POST.get('duration')
        flight.price = request.POST.get('price')
        flight.price_category = request.POST.get('price_category')
        flight.available_seats = request.POST.get('available_seats')
        flight.is_active = request.POST.get('is_active') == 'on'
        flight.save()
        messages.success(request, 'Flight updated successfully')
        return redirect('admin_page')

    return render(request, 'edit_flight.html', {'flight': flight})


@staff_member_required(login_url='login')
def admin_delete_flight(request, flight_id):
    try:
        flight = Flight.objects.get(id=flight_id)
        flight.delete()
        messages.success(request, 'Flight deleted successfully')
    except Flight.DoesNotExist:
        messages.error(request, 'Flight not found')
    return redirect('admin_page')


# ===== PACKAGE MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_add_package(request):
    if request.method == 'POST':
        Package.objects.create(
            name=request.POST.get('name'),
            duration_days=request.POST.get('duration_days'),
            includes=request.POST.get('includes'),
            description=request.POST.get('description'),
            image_url=request.POST.get('image_url'),
            price_per_person=request.POST.get('price_per_person'),
            discount_percentage=request.POST.get('discount_percentage', 0),
            is_active=True
        )
        messages.success(request, 'Package added successfully')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_edit_package(request, package_id):
    package = get_object_or_404(Package, id=package_id)
    if request.method == 'POST':
        package.name = request.POST.get('name')
        package.duration_days = request.POST.get('duration_days')
        package.includes = request.POST.get('includes')
        package.description = request.POST.get('description')
        package.image_url = request.POST.get('image_url')
        package.price_per_person = request.POST.get('price_per_person')
        package.discount_percentage = request.POST.get('discount_percentage', 0)
        package.is_active = request.POST.get('is_active') == 'on'
        package.save()
        messages.success(request, 'Package updated successfully')
        return redirect('admin_page')

    return render(request, 'edit_package.html', {'package': package})


@staff_member_required(login_url='login')
def admin_delete_package(request, package_id):
    try:
        package = Package.objects.get(id=package_id)
        package.delete()
        messages.success(request, 'Package deleted successfully')
    except Package.DoesNotExist:
        messages.error(request, 'Package not found')
    return redirect('admin_page')


# ===== REVIEW MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_approve_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        review.is_approved = True
        review.save()
        messages.success(request, 'Review approved successfully')
    except Review.DoesNotExist:
        messages.error(request, 'Review not found')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_delete_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        review.delete()
        messages.success(request, 'Review deleted successfully')
    except Review.DoesNotExist:
        messages.error(request, 'Review not found')
    return redirect('admin_page')


# ===== CONTACT MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_mark_resolved(request, contact_id):
    try:
        contact = Contact.objects.get(id=contact_id)
        contact.is_resolved = True
        contact.save()
        messages.success(request, 'Contact marked as resolved')
    except Contact.DoesNotExist:
        messages.error(request, 'Contact not found')
    return redirect('admin_page')


# ===== BOOKING MANAGEMENT =====
@staff_member_required(login_url='login')
def admin_view_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'view_booking.html', {'booking': booking})


@staff_member_required(login_url='login')
def admin_update_booking_status(request, booking_id):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(id=booking_id)
            new_status = request.POST.get('status')
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking status updated to {new_status}')
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found')
    return redirect('admin_page')


@staff_member_required(login_url='login')
def admin_delete_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        messages.success(request, 'Booking deleted successfully')
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
    return redirect('admin_page')

# ===== PAYMENT VIEWS =====
@login_required(login_url='login')
def payment_page(request, booking_id):
    """Payment page for a specific booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Calculate days until due
    days_until_due = (booking.payment_due_date - timezone.now().date()).days if booking.payment_due_date else 7

    context = {
        'booking': booking,
        'days_until_due': days_until_due,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,  # Add this to settings
    }
    return render(request, 'payment.html', context)

# ... rest of your code ...

@login_required(login_url='login')
def process_payment(request, booking_id):
    """Process payment for a booking"""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        # Get payment details from form
        payment_method = request.POST.get('payment_method')

        # Fix: Convert to Decimal instead of float
        amount_str = request.POST.get('amount', str(booking.remaining_amount))
        try:
            amount = Decimal(str(amount_str))
        except:
            messages.error(request, 'Invalid payment amount')
            return redirect('payment_page', booking_id=booking.id)

        # Validate amount
        if amount <= 0:
            messages.error(request, 'Invalid payment amount')
            return redirect('payment_page', booking_id=booking.id)

        if amount > booking.remaining_amount:
            messages.error(request, f'Amount exceeds remaining balance of ${booking.remaining_amount}')
            return redirect('payment_page', booking_id=booking.id)

        try:
            # Simulate payment processing
            transaction_id = f"TXN-{generate_ticket_number()}"

            # Update booking payment status - now using Decimal
            booking.amount_paid += amount
            booking.remaining_amount = booking.total_price - booking.amount_paid

            if booking.remaining_amount <= 0:
                booking.payment_status = 'completed'
                booking.status = 'confirmed'
            else:
                booking.payment_status = 'partial'

            booking.payment_method = payment_method
            booking.transaction_id = transaction_id
            booking.payment_date = timezone.now()
            booking.save()

            messages.success(request, f'Payment successful! Transaction ID: {transaction_id}')
            return redirect('booking_detail', booking_id=booking.id)

        except Exception as e:
            messages.error(request, f'Payment failed: {str(e)}')
            return redirect('payment_page', booking_id=booking.id)

    return redirect('my_bookings')



@login_required(login_url='login')
def booking_detail(request, booking_id):
    """View booking details with payment info"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking_detail.html', {'booking': booking})


@login_required(login_url='login')
def make_partial_payment(request, booking_id):
    """Make a partial payment towards a booking"""
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        amount = float(request.POST.get('amount', 0))

        if amount <= 0:
            messages.error(request, 'Invalid payment amount')
        elif amount > booking.remaining_amount:
            messages.error(request, f'Amount exceeds remaining balance of ${booking.remaining_amount}')
        else:
            # Process partial payment
            transaction_id = f"PART-{generate_ticket_number()}"
            booking.amount_paid += amount
            booking.remaining_amount = booking.total_price - booking.amount_paid
            booking.payment_status = 'partial' if booking.remaining_amount > 0 else 'completed'
            booking.transaction_id = transaction_id
            booking.payment_date = timezone.now()
            booking.save()

            messages.success(request, f'Partial payment of ${amount} successful!')

        return redirect('booking_detail', booking_id=booking.id)

    return redirect('my_bookings')


def send_payment_confirmation_email(booking):
    """Send payment confirmation email"""
    subject = f'Payment Confirmed - {booking.ticket_number}'
    message = f"""
    Dear {booking.full_name},

    Your payment of ${booking.amount_paid} has been confirmed.

    Booking Details:
    - Ticket Number: {booking.ticket_number}
    - Item: {booking.item_name}
    - Total Amount: ${booking.total_price}
    - Amount Paid: ${booking.amount_paid}
    - Remaining: ${booking.remaining_amount}
    - Payment Status: {booking.get_payment_status_display()}

    Thank you for choosing Tower Travel!
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.email],
            fail_silently=True,
        )
    except:
        pass  # Silently fail if email not configured


# ==================== AI MODULE FUNCTIONS ====================
import json
from django.http import JsonResponse
from django.db.models import Q


def ai_recommendations_api(request):
    """API endpoint for AI recommendations"""
    rec_type = request.GET.get('type', 'all')
    budget = request.GET.get('budget', '')
    search = request.GET.get('search', '')

    recommendations = []

    # Get destinations
    if rec_type == 'all' or rec_type == 'destination':
        destinations = Destination.objects.filter(is_active=True)
        if budget:
            destinations = destinations.filter(budget=budget)
        if search:
            destinations = destinations.filter(
                Q(name__icontains=search) | Q(country__icontains=search)
            )
        for dest in destinations[:10]:
            recommendations.append({
                'type': 'destination',
                'name': dest.name,
                'country': dest.country,
                'category': dest.category,
                'budget': dest.budget,
                'price': float(dest.price_per_day),
                'description': dest.description[:100],
                'image': dest.image_url,
                'weather': get_weather_for_country(dest.country),
                'rating': 4.5,
            })

    # Get hotels
    if rec_type == 'all' or rec_type == 'hotel':
        hotels = Hotel.objects.all()
        if budget:
            hotels = hotels.filter(price_category=budget)
        if search:
            hotels = hotels.filter(name__icontains=search)
        for hotel in hotels[:10]:
            recommendations.append({
                'type': 'hotel',
                'name': hotel.name,
                'location': hotel.location,
                'budget': hotel.price_category,
                'price': float(hotel.price_per_night),
                'rating': hotel.rating,
                'amenities': hotel.amenities[:50],
                'image': hotel.image_url,
            })

    # Get flights
    if rec_type == 'all' or rec_type == 'flight':
        flights = Flight.objects.filter(is_active=True)
        if budget:
            flights = flights.filter(price_category=budget)
        if search:
            flights = flights.filter(
                Q(airline__icontains=search) |
                Q(from_city__icontains=search) |
                Q(to_city__icontains=search)
            )
        for flight in flights[:10]:
            recommendations.append({
                'type': 'flight',
                'airline': flight.get_airline_display(),
                'flight_number': flight.flight_number,
                'from': flight.from_city,
                'to': flight.to_city,
                'budget': flight.price_category,
                'price': float(flight.price),
                'duration': flight.duration,
                'departure': flight.departure_time.strftime('%H:%M'),
                'arrival': flight.arrival_time.strftime('%H:%M'),
                'weather': get_weather_for_city(flight.to_city),
            })

    # Get packages
    if rec_type == 'all' or rec_type == 'package':
        packages = Package.objects.filter(is_active=True)
        if search:
            packages = packages.filter(name__icontains=search)
        for package in packages[:10]:
            recommendations.append({
                'type': 'package',
                'name': package.name,
                'duration': package.duration_days,
                'price': float(package.discounted_price),
                'original_price': float(package.price_per_person),
                'discount': package.discount_percentage,
                'includes': package.includes[:50],
                'image': package.image_url,
            })

    # Sort by price if budget filter is applied
    if budget:
        recommendations.sort(key=lambda x: x.get('price', 0))

    return JsonResponse({'recommendations': recommendations[:20]})


def ai_chatbot_api(request):
    """API endpoint for AI chatbot"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').lower()

            response = generate_ai_response(message, request.user, request)  # Pass request here
            return JsonResponse({'response': response})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def generate_ai_response(message, user, request=None):
    """Generate AI response based on user message with REAL database booking capabilities"""

    message_lower = message.lower()
    import re

    # ==================== BOOKING FLOW ====================

    # Check if user wants to book
    if any(word in message_lower for word in
           ['book', 'reserve', 'booking', 'want to book', 'i want to book', 'book now']):
        # Check what type of booking they want
        if 'destination' in message_lower or 'place' in message_lower or 'beach' in message_lower or 'mountain' in message_lower or 'city' in message_lower:
            # Show available destinations from REAL database
            destinations = Destination.objects.filter(is_active=True)[:5]
            response = "🌍 **Available Destinations to Book:**\n\n"
            for dest in destinations:
                response += f"• **{dest.name}** ({dest.country}) - ${dest.price_per_day}/day - {dest.category}\n"
            response += "\nTo book, reply with: \"Book [destination name] on [YYYY-MM-DD] for [number] people\"\n"
            response += "Example: \"Book Beach Paradise on 2025-06-15 for 2 people\""
            return response

        elif 'hotel' in message_lower or 'stay' in message_lower or 'room' in message_lower:
            # Show available hotels from REAL database
            hotels = Hotel.objects.filter(available_rooms__gt=0)[:5]
            response = "🏨 **Available Hotels to Book:**\n\n"
            for hotel in hotels:
                response += f"• **{hotel.name}** ({hotel.location}) - ${hotel.price_per_night}/night ⭐ {hotel.rating}★\n"
                response += f"  📍 {hotel.amenities[:50]}...\n"
            response += "\nTo book, reply with: \"Book [hotel name] from [check-in] to [check-out] for [rooms] rooms\"\n"
            response += "Example: \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\""
            return response

        elif 'flight' in message_lower or 'fly' in message_lower or 'airline' in message_lower:
            # Show available flights from REAL database
            flights = Flight.objects.filter(is_active=True, available_seats__gt=0)[:5]
            response = "✈️ **Available Flights to Book:**\n\n"
            for flight in flights:
                response += f"• **{flight.get_airline_display()}** {flight.flight_number}: {flight.from_city} → {flight.to_city}\n"
                response += f"  🕐 {flight.departure_time} | 💰 ${flight.price} | {flight.available_seats} seats left\n"
            response += "\nTo book, reply with: \"Book [airline/flight] on [date] for [number] passengers\"\n"
            response += "Example: \"Book Emirates EK001 on 2025-06-15 for 2 passengers\""
            return response

        elif 'package' in message_lower or 'tour' in message_lower or 'deal' in message_lower:
            # Show available packages from REAL database
            packages = Package.objects.filter(is_active=True)[:5]
            response = "🎒 **Available Packages to Book:**\n\n"
            for pkg in packages:
                if pkg.discount_percentage > 0:
                    response += f"• **{pkg.name}** ({pkg.duration_days} days) - ${pkg.discounted_price} (Was ${pkg.price_per_person})\n"
                else:
                    response += f"• **{pkg.name}** ({pkg.duration_days} days) - ${pkg.price_per_person}\n"
                response += f"  ✨ {pkg.includes}\n"
            response += "\nTo book, reply with: \"Book [package name] starting [date] for [number] people\"\n"
            response += "Example: \"Book Family Package starting 2025-06-15 for 4 people\""
            return response

        else:
            return "✈️ What would you like to book?\n\n• 🏖️ Destination\n• 🏨 Hotel\n• ✈️ Flight\n• 🎒 Package\n\nPlease specify what you'd like to book!"

    # ==================== EXTRACT BOOKING DETAILS FROM USER MESSAGE ====================

    # Destination Booking - REAL DATA
    if 'book' in message_lower and (
            'destination' in message_lower or 'place' in message_lower or 'beach' in message_lower or 'mountain' in message_lower):
        # Search for destination in REAL database
        for dest in Destination.objects.filter(is_active=True):
            if dest.name.lower() in message_lower:
                # Extract date
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', message)
                if date_match:
                    travel_date = date_match.group()
                    # Extract number of people
                    people_match = re.search(r'(\d+)\s*people', message_lower) or re.search(r'for\s*(\d+)',
                                                                                            message_lower)
                    people = int(people_match.group(1)) if people_match else 2

                    total_price = float(dest.price_per_day) * people

                    # Store in session for confirmation
                    if request:
                        request.session['pending_booking'] = {
                            'type': 'destination',
                            'item_id': dest.id,
                            'item_name': dest.name,
                            'country': dest.country,
                            'travel_date': travel_date,
                            'people': people,
                            'price_per_day': float(dest.price_per_day),
                            'total_price': total_price
                        }

                    return f"🌟 **Booking Summary:**\n\n" \
                           f"📍 Destination: {dest.name} ({dest.country})\n" \
                           f"📅 Travel Date: {travel_date}\n" \
                           f"👥 People: {people}\n" \
                           f"💰 Price: ${dest.price_per_day}/day\n" \
                           f"💰 Total: ${total_price}\n\n" \
                           f"✅ **Confirm this booking?** Reply with \"CONFIRM\" or \"YES\" to proceed."
                else:
                    return f"📅 Please provide a travel date in YYYY-MM-DD format.\n\nExample: \"Book {dest.name} on 2025-06-15 for 2 people\""

        return "❌ Destination not found. Please check the name and try again.\n\nAvailable destinations:\n" + \
            "\n".join([f"• {d.name} ({d.country})" for d in Destination.objects.filter(is_active=True)[:5]])

    # Hotel Booking - REAL DATA
    elif 'book' in message_lower and 'hotel' in message_lower:
        for hotel in Hotel.objects.filter(available_rooms__gt=0):
            if hotel.name.lower() in message_lower:
                # Extract dates
                dates = re.findall(r'\d{4}-\d{2}-\d{2}', message)
                if len(dates) >= 2:
                    check_in, check_out = dates[0], dates[1]
                    # Calculate nights
                    nights = (datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days
                    if nights <= 0:
                        return "❌ Check-out date must be after check-in date."

                    # Extract rooms
                    rooms_match = re.search(r'(\d+)\s*rooms', message_lower)
                    rooms = int(rooms_match.group(1)) if rooms_match else 1

                    # Extract guests
                    guests_match = re.search(r'(\d+)\s*guests', message_lower)
                    guests = int(guests_match.group(1)) if guests_match else 2

                    total_price = float(hotel.price_per_night) * nights * rooms

                    if request:
                        request.session['pending_booking'] = {
                            'type': 'hotel',
                            'item_id': hotel.id,
                            'item_name': hotel.name,
                            'location': hotel.location,
                            'check_in': check_in,
                            'check_out': check_out,
                            'nights': nights,
                            'rooms': rooms,
                            'guests': guests,
                            'price_per_night': float(hotel.price_per_night),
                            'total_price': total_price
                        }

                    return f"🏨 **Booking Summary:**\n\n" \
                           f"Hotel: {hotel.name} ({hotel.location})\n" \
                           f"⭐ Rating: {hotel.rating}★\n" \
                           f"📅 Check-in: {check_in}\n" \
                           f"📅 Check-out: {check_out}\n" \
                           f"🏠 Nights: {nights}\n" \
                           f"🚪 Rooms: {rooms}\n" \
                           f"👥 Guests: {guests}\n" \
                           f"💰 Price: ${hotel.price_per_night}/night\n" \
                           f"💰 Total: ${total_price}\n\n" \
                           f"✅ **Confirm this booking?** Reply with \"CONFIRM\" or \"YES\" to proceed."
                else:
                    return f"📅 Please provide check-in and check-out dates in YYYY-MM-DD format.\n\nExample: \"Book {hotel.name} from 2025-06-15 to 2025-06-18 for 2 rooms\""

        return "❌ Hotel not found or fully booked. Please check the name and try again.\n\nAvailable hotels:\n" + \
            "\n".join([f"• {h.name} ({h.location}) - {h.available_rooms} rooms left" for h in
                       Hotel.objects.filter(available_rooms__gt=0)[:5]])

    # Flight Booking - REAL DATA
    elif 'book' in message_lower and 'flight' in message_lower:
        for flight in Flight.objects.filter(is_active=True, available_seats__gt=0):
            flight_display = f"{flight.get_airline_display()} {flight.flight_number}".lower()
            if flight_display in message_lower or flight.flight_number.lower() in message_lower:
                # Extract date
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', message)
                if date_match:
                    travel_date = date_match.group()
                    # Extract passengers
                    passengers_match = re.search(r'(\d+)\s*passengers', message_lower) or re.search(r'(\d+)\s*people',
                                                                                                    message_lower)
                    passengers = int(passengers_match.group(1)) if passengers_match else 1

                    if passengers > flight.available_seats:
                        return f"❌ Only {flight.available_seats} seats available for this flight. Please reduce the number of passengers."

                    total_price = float(flight.price) * passengers

                    if request:
                        request.session['pending_booking'] = {
                            'type': 'flight',
                            'item_id': flight.id,
                            'item_name': f"{flight.get_airline_display()} {flight.flight_number}",
                            'from_city': flight.from_city,
                            'to_city': flight.to_city,
                            'travel_date': travel_date,
                            'departure_time': flight.departure_time.strftime('%H:%M'),
                            'arrival_time': flight.arrival_time.strftime('%H:%M'),
                            'passengers': passengers,
                            'price': float(flight.price),
                            'total_price': total_price
                        }

                    return f"✈️ **Booking Summary:**\n\n" \
                           f"Airline: {flight.get_airline_display()} {flight.flight_number}\n" \
                           f"📍 From: {flight.from_city} → To: {flight.to_city}\n" \
                           f"📅 Date: {travel_date}\n" \
                           f"🕐 Departure: {flight.departure_time} | Arrival: {flight.arrival_time}\n" \
                           f"⏱️ Duration: {flight.duration}\n" \
                           f"👥 Passengers: {passengers}\n" \
                           f"💰 Price: ${flight.price}/passenger\n" \
                           f"💰 Total: ${total_price}\n\n" \
                           f"✅ **Confirm this booking?** Reply with \"CONFIRM\" or \"YES\" to proceed."
                else:
                    return f"📅 Please provide a travel date in YYYY-MM-DD format.\n\nExample: \"Book {flight.get_airline_display()} {flight.flight_number} on 2025-06-15 for 2 passengers\""

        return "✈️ Flight not found. Please check the flight number and try again.\n\nAvailable flights:\n" + \
            "\n".join([f"• {f.get_airline_display()} {f.flight_number}: {f.from_city} → {f.to_city}" for f in
                       Flight.objects.filter(is_active=True, available_seats__gt=0)[:5]])

    # Package Booking - REAL DATA
    elif 'book' in message_lower and 'package' in message_lower:
        for package in Package.objects.filter(is_active=True):
            if package.name.lower() in message_lower:
                # Extract date
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', message)
                if date_match:
                    start_date = date_match.group()
                    # Extract number of people
                    people_match = re.search(r'(\d+)\s*people', message_lower)
                    people = int(people_match.group(1)) if people_match else 2

                    if people > package.max_people:
                        return f"❌ This package supports maximum {package.max_people} people. Please reduce the number."

                    total_price = float(package.discounted_price) * people

                    if request:
                        request.session['pending_booking'] = {
                            'type': 'package',
                            'item_id': package.id,
                            'item_name': package.name,
                            'start_date': start_date,
                            'duration': package.duration_days,
                            'people': people,
                            'price_per_person': float(package.discounted_price),
                            'total_price': total_price
                        }

                    discount_text = f" (Was ${package.price_per_person})" if package.discount_percentage > 0 else ""
                    return f"🎒 **Booking Summary:**\n\n" \
                           f"Package: {package.name}\n" \
                           f"📅 Duration: {package.duration_days} days\n" \
                           f"📅 Start Date: {start_date}\n" \
                           f"👥 People: {people}\n" \
                           f"💰 Price: ${package.discounted_price}/person{discount_text}\n" \
                           f"✨ Includes: {package.includes}\n" \
                           f"💰 Total: ${total_price}\n\n" \
                           f"✅ **Confirm this booking?** Reply with \"CONFIRM\" or \"YES\" to proceed."
                else:
                    return f"📅 Please provide a start date in YYYY-MM-DD format.\n\nExample: \"Book {package.name} starting 2025-06-15 for 4 people\""

        return "🎒 Package not found. Please check the package name and try again.\n\nAvailable packages:\n" + \
            "\n".join([f"• {p.name} ({p.duration_days} days)" for p in Package.objects.filter(is_active=True)[:5]])

    # ==================== BOOKING CONFIRMATION ====================

    if message_lower in ['confirm', 'yes', 'confirm booking', 'yes book', 'confirm', 'yes', 'confirm it', 'book it']:
        if request and request.session.get('pending_booking'):
            pending = request.session.get('pending_booking')

            try:
                if pending['type'] == 'destination':
                    # Get the actual destination object
                    dest = Destination.objects.get(id=pending['item_id'])

                    booking = Booking.objects.create(
                        user=user,
                        booking_type='destination',
                        item_id=pending['item_id'],
                        item_name=pending['item_name'],
                        item_details=f"Destination: {pending['item_name']}, Country: {pending.get('country', 'N/A')}",
                        travel_date=pending['travel_date'],
                        number_of_people=pending['people'],
                        price_per_unit=pending['price_per_day'],
                        total_price=pending['total_price'],
                        full_name=user.get_full_name() or user.username,
                        email=user.email,
                        ticket_number=generate_ticket_number(),
                        status='confirmed',
                        payment_status='pending',
                        amount_paid=0,
                        remaining_amount=pending['total_price'],
                        payment_due_date=timezone.now().date() + timedelta(days=7)
                    )

                elif pending['type'] == 'hotel':
                    hotel = Hotel.objects.get(id=pending['item_id'])
                    # Update hotel availability
                    hotel.available_rooms -= pending['rooms']
                    hotel.save()

                    booking = Booking.objects.create(
                        user=user,
                        booking_type='hotel',
                        item_id=pending['item_id'],
                        item_name=pending['item_name'],
                        item_details=f"Hotel: {pending['item_name']}, Location: {pending.get('location', 'N/A')}",
                        travel_date=pending['check_in'],
                        return_date=pending['check_out'],
                        number_of_people=pending['guests'],
                        number_of_rooms=pending['rooms'],
                        price_per_unit=pending['price_per_night'],
                        total_price=pending['total_price'],
                        full_name=user.get_full_name() or user.username,
                        email=user.email,
                        ticket_number=generate_ticket_number(),
                        status='confirmed',
                        payment_status='pending',
                        amount_paid=0,
                        remaining_amount=pending['total_price'],
                        payment_due_date=timezone.now().date() + timedelta(days=7)
                    )

                elif pending['type'] == 'flight':
                    flight = Flight.objects.get(id=pending['item_id'])
                    # Update flight availability
                    flight.available_seats -= pending['passengers']
                    flight.save()

                    booking = Booking.objects.create(
                        user=user,
                        booking_type='flight',
                        item_id=pending['item_id'],
                        item_name=pending['item_name'],
                        item_details=f"Flight: {pending['item_name']}, {pending['from_city']} → {pending['to_city']}",
                        travel_date=pending['travel_date'],
                        number_of_people=pending['passengers'],
                        price_per_unit=pending['price'],
                        total_price=pending['total_price'],
                        full_name=user.get_full_name() or user.username,
                        email=user.email,
                        ticket_number=generate_ticket_number(),
                        status='confirmed',
                        payment_status='pending',
                        amount_paid=0,
                        remaining_amount=pending['total_price'],
                        payment_due_date=timezone.now().date() + timedelta(days=7)
                    )

                elif pending['type'] == 'package':
                    booking = Booking.objects.create(
                        user=user,
                        booking_type='package',
                        item_id=pending['item_id'],
                        item_name=pending['item_name'],
                        item_details=f"Package: {pending['item_name']}, Duration: {pending['duration']} days",
                        travel_date=pending['start_date'],
                        number_of_people=pending['people'],
                        price_per_unit=pending['price_per_person'],
                        total_price=pending['total_price'],
                        full_name=user.get_full_name() or user.username,
                        email=user.email,
                        ticket_number=generate_ticket_number(),
                        status='confirmed',
                        payment_status='pending',
                        amount_paid=0,
                        remaining_amount=pending['total_price'],
                        payment_due_date=timezone.now().date() + timedelta(days=7)
                    )

                # Clear the pending booking
                del request.session['pending_booking']

                return f"✅ **Booking Confirmed!** 🎉\n\n" \
                       f"📋 Booking Details:\n" \
                       f"• Ticket Number: {booking.ticket_number}\n" \
                       f"• Item: {booking.item_name}\n" \
                       f"• Total Amount: ${booking.total_price}\n" \
                       f"• Payment Due: {booking.payment_due_date.strftime('%B %d, %Y')}\n\n" \
                       f"💰 **Payment Status:** {booking.get_payment_status_display()}\n" \
                       f"💳 Please complete payment within 7 days to confirm your booking.\n\n" \
                       f"Thank you for choosing Tower Travel! 🌟"

            except Exception as e:
                return f"❌ Sorry, there was an error processing your booking: {str(e)}"
        else:
            return "✨ Please provide the booking details first. Tell me what you'd like to book (destination, hotel, flight, or package)."

    # ==================== EXISTING CHATBOT RESPONSES ====================

    # Get cheapest options from database
    cheapest_dest = Destination.objects.filter(is_active=True).order_by('price_per_day').first()
    cheapest_hotel = Hotel.objects.all().order_by('price_per_night').first()
    cheapest_flight = Flight.objects.filter(is_active=True).order_by('price').first()

    # Budget-related queries
    if any(word in message_lower for word in ['budget', 'cheap', 'affordable', 'cost', 'price', 'low cost']):
        response = "💰 **Budget-Friendly Options:**\n\n"
        if cheapest_dest:
            response += f"🏖️ **Destinations:** {cheapest_dest.name} from ${cheapest_dest.price_per_day}/day\n"
        if cheapest_hotel:
            response += f"🏨 **Hotels:** {cheapest_hotel.name} from ${cheapest_hotel.price_per_night}/night\n"
        if cheapest_flight:
            response += f"✈️ **Flights:** {cheapest_flight.get_airline_display()} from ${cheapest_flight.price}\n\n"
        response += "Would you like to book any of these? Just say 'book' followed by the item name!"
        return response

    # Destination queries with booking option
    elif any(word in message_lower for word in ['destination', 'place', 'visit', 'go', 'travel to', 'where']):
        popular_dest = Destination.objects.filter(is_active=True).order_by('?')[:3]
        response = "🌍 **Top Destinations Recommended for You:**\n\n"
        for dest in popular_dest:
            response += f"• **{dest.name}**, {dest.country} - ${dest.price_per_day}/day ({dest.category})\n"
        response += "\nTo book, say: \"Book [destination name] on [date] for [number] people\"\nExample: \"Book Beach Paradise on 2025-06-15 for 2 people\""
        return response

    # Hotel queries with booking option
    elif any(word in message_lower for word in ['hotel', 'stay', 'accommodation', 'room', 'lodge']):
        hotels = Hotel.objects.filter(available_rooms__gt=0).order_by('-rating')[:5]
        response = "🏨 **Available Hotels:**\n\n"
        for hotel in hotels:
            response += f"• **{hotel.name}** ({hotel.location}) - ${hotel.price_per_night}/night ⭐ {hotel.rating}★ - {hotel.available_rooms} rooms left\n"
        response += "\nTo book, say: \"Book [hotel name] from [check-in] to [check-out] for [rooms] rooms\"\nExample: \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\""
        return response

    # Flight queries with booking option
    elif any(word in message_lower for word in ['flight', 'fly', 'airline', 'plane', 'air']):
        flights = Flight.objects.filter(is_active=True, available_seats__gt=0).order_by('price')[:5]
        response = "✈️ **Available Flights:**\n\n"
        for flight in flights:
            response += f"• **{flight.get_airline_display()}** {flight.flight_number}: {flight.from_city} → {flight.to_city}\n"
            response += f"  🕐 {flight.departure_time} | 💰 ${flight.price} | {flight.available_seats} seats left\n\n"
        response += "To book, say: \"Book [airline/flight] on [date] for [number] passengers\"\nExample: \"Book Emirates EK001 on 2025-06-15 for 2 passengers\""
        return response

    # Package queries with booking option
    elif any(word in message_lower for word in ['package', 'deal', 'tour', 'bundle', 'vacation']):
        packages = Package.objects.filter(is_active=True)[:5]
        response = "🎒 **Tour Packages:**\n\n"
        for pkg in packages:
            if pkg.discount_percentage > 0:
                response += f"• **{pkg.name}** ({pkg.duration_days} days) - ${pkg.discounted_price} (Was ${pkg.price_per_person})\n"
            else:
                response += f"• **{pkg.name}** ({pkg.duration_days} days) - ${pkg.price_per_person}\n"
            response += f"  ✨ {pkg.includes}\n\n"
        response += "To book, say: \"Book [package name] starting [date] for [number] people\"\nExample: \"Book Family Package starting 2025-06-15 for 4 people\""
        return response

    # Weather queries
    elif 'weather' in message_lower:
        popular_cities = ['Dubai', 'Paris', 'New York', 'London', 'Tokyo']
        response = "☁️ **Weather Updates:**\n\n"
        for city in popular_cities:
            response += f"• {city}: {get_weather_for_city(city)}\n"
        response += "\nNeed weather for a specific destination? Just ask!"
        return response

    # Reviews queries
    elif any(word in message_lower for word in ['review', 'rating', 'feedback']):
        reviews = Review.objects.filter(is_approved=True).order_by('-rating')[:5]
        response = "⭐ **Top Rated Experiences:**\n\n"
        for review in reviews:
            response += f"• **{review.name}** - {review.review_type}: {review.rating}★\n"
            response += f"  \"{review.text[:80]}...\"\n\n"
        return response

    # Help/General
    elif any(word in message_lower for word in ['help', 'what can you do', 'assist', 'support']):
        return "🤖 **I can help you with:**\n\n" \
               "✅ **BOOK** destinations, hotels, flights, and packages\n" \
               "✅ Find destinations by budget\n" \
               "✅ Recommend hotels and accommodations\n" \
               "✅ Show available flights\n" \
               "✅ Discover tour packages\n" \
               "✅ Show reviews and ratings\n" \
               "✅ Check weather forecasts\n\n" \
               "**How to book:**\n" \
               "• 🏖️ \"Book Beach Paradise on 2025-06-15 for 2 people\"\n" \
               "• 🏨 \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\"\n" \
               "• ✈️ \"Book Emirates EK001 on 2025-06-15 for 2 passengers\"\n" \
               "• 🎒 \"Book Family Package starting 2025-06-15 for 4 people\"\n\n" \
               "What would you like to book today?"

    # Default response
    else:
        return "🌟 **Welcome to Tower Travel AI Assistant!**\n\n" \
               "I can help you **BOOK** travel options and find the best deals.\n\n" \
               "**Try these commands:**\n" \
               "• 🏖️ \"Book Beach Paradise on 2025-06-15 for 2 people\"\n" \
               "• 🏨 \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\"\n" \
               "• ✈️ \"Find cheap flights to London\"\n" \
               "• 🎒 \"Show me family packages\"\n\n" \
               "What would you like to book?"



def get_weather_for_country(country):
    """Get weather for country"""
    weather_data = {
        'Maldives': 'Sunny, 28°C ☀️',
        'Switzerland': 'Cool, 15°C ⛅',
        'USA': 'Moderate, 22°C 🌤️',
        'Japan': 'Mild, 20°C 🌸',
        'UAE': 'Hot, 32°C 🔥',
        'France': 'Mild, 18°C 🌹',
        'Thailand': 'Warm, 30°C ☀️',
        'Italy': 'Pleasant, 24°C 🍝',
        'UK': 'Cloudy, 18°C ☁️',
        'Canada': 'Cool, 16°C 🍁',
    }
    return weather_data.get(country, 'Pleasant weather, 22°C 🌤️')


def get_weather_for_city(city):
    """Get weather for city"""
    weather_data = {
        'Dubai': 'Sunny, 32°C ☀️',
        'London': 'Cloudy, 18°C ☁️',
        'Paris': 'Mild, 20°C 🌹',
        'New York': 'Moderate, 22°C 🗽',
        'Tokyo': 'Mild, 20°C 🌸',
        'Karachi': 'Warm, 28°C 🌊',
        'Istanbul': 'Pleasant, 24°C 🕌',
        'Rome': 'Sunny, 25°C 🏛️',
        'Bangkok': 'Hot, 32°C 🍜',
        'Sydney': 'Sunny, 24°C 🏖️',
    }
    return weather_data.get(city, 'Pleasant weather, 22°C 🌤️')


# ==================== AI BOOKING FUNCTIONS ====================

def ai_handle_booking(request):
    """Handle booking requests from AI chatbot"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booking_type = data.get('booking_type')
            item_id = data.get('item_id')
            travel_date = data.get('travel_date')
            people = data.get('people', 1)
            full_name = data.get('full_name', request.user.get_full_name() or request.user.username)
            email = data.get('email', request.user.email)
            phone = data.get('phone', '')
            special_requests = data.get('special_requests', '')

            # Get item details based on type
            if booking_type == 'destination':
                item = get_object_or_404(Destination, id=item_id)
                price = float(item.price_per_day)
                item_name = item.name
                total_price = price * people
                item_details = f"Destination: {item.name}, Country: {item.country}"

            elif booking_type == 'hotel':
                item = get_object_or_404(Hotel, id=item_id)
                price = float(item.price_per_night)
                item_name = item.name
                check_out = data.get('check_out_date')
                nights = (datetime.strptime(check_out, '%Y-%m-%d').date() - datetime.strptime(travel_date,
                                                                                              '%Y-%m-%d').date()).days
                total_price = price * nights * people
                item_details = f"Hotel: {item.name}, Location: {item.location}, {nights} nights"

            elif booking_type == 'flight':
                item = get_object_or_404(Flight, id=item_id)
                price = float(item.price)
                item_name = f"{item.get_airline_display()} {item.flight_number}"
                total_price = price * people
                item_details = f"Flight: {item.get_airline_display()} {item.flight_number}, {item.from_city} → {item.to_city}"

            elif booking_type == 'package':
                item = get_object_or_404(Package, id=item_id)
                price = float(item.discounted_price)
                item_name = item.name
                total_price = price * people
                item_details = f"Package: {item.name}, Duration: {item.duration_days} days"

            else:
                return JsonResponse({'success': False, 'error': 'Invalid booking type'}, status=400)

            # Create booking
            ticket_number = generate_ticket_number()
            booking = Booking.objects.create(
                user=request.user,
                booking_type=booking_type,
                item_id=item_id,
                item_name=item_name,
                item_details=item_details,
                travel_date=travel_date,
                return_date=data.get('return_date') if booking_type == 'hotel' else None,
                number_of_people=people,
                number_of_rooms=data.get('rooms', 1) if booking_type == 'hotel' else 1,
                price_per_unit=price,
                total_price=total_price,
                full_name=full_name,
                email=email,
                phone=phone,
                special_requests=special_requests,
                ticket_number=ticket_number,
                status='confirmed',
                payment_status='pending',
                amount_paid=0,
                remaining_amount=total_price,
                payment_due_date=timezone.now().date() + timedelta(days=7)
            )

            # Update availability
            if booking_type == 'hotel':
                item.available_rooms -= data.get('rooms', 1)
                item.save()
            elif booking_type == 'flight':
                item.available_seats -= people
                item.save()

            return JsonResponse({
                'success': True,
                'message': f'✅ Booking confirmed! Your ticket number is {ticket_number}',
                'booking_id': booking.id,
                'ticket_number': ticket_number,
                'total_price': total_price,
                'payment_due_date': booking.payment_due_date.strftime('%Y-%m-%d')
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def ai_get_available_items(request):
    """Get available items for booking"""
    item_type = request.GET.get('type', '')
    budget = request.GET.get('budget', '')

    items = []

    if item_type == 'destination' or item_type == 'all':
        destinations = Destination.objects.filter(is_active=True)
        if budget:
            destinations = destinations.filter(budget=budget)
        for dest in destinations[:10]:
            items.append({
                'type': 'destination',
                'id': dest.id,
                'name': dest.name,
                'country': dest.country,
                'price': float(dest.price_per_day),
                'budget': dest.budget,
                'description': dest.description[:100]
            })

    if item_type == 'hotel' or item_type == 'all':
        hotels = Hotel.objects.filter(available_rooms__gt=0)
        if budget:
            hotels = hotels.filter(price_category=budget)
        for hotel in hotels[:10]:
            items.append({
                'type': 'hotel',
                'id': hotel.id,
                'name': hotel.name,
                'location': hotel.location,
                'price': float(hotel.price_per_night),
                'rating': hotel.rating,
                'available_rooms': hotel.available_rooms,
                'amenities': hotel.amenities[:50]
            })

    if item_type == 'flight' or item_type == 'all':
        flights = Flight.objects.filter(is_active=True, available_seats__gt=0)
        if budget:
            flights = flights.filter(price_category=budget)
        for flight in flights[:10]:
            items.append({
                'type': 'flight',
                'id': flight.id,
                'airline': flight.get_airline_display(),
                'flight_number': flight.flight_number,
                'from': flight.from_city,
                'to': flight.to_city,
                'price': float(flight.price),
                'departure_date': flight.departure_date.strftime('%Y-%m-%d'),
                'departure_time': flight.departure_time.strftime('%H:%M'),
                'available_seats': flight.available_seats
            })

    if item_type == 'package' or item_type == 'all':
        packages = Package.objects.filter(is_active=True)
        for package in packages[:10]:
            items.append({
                'type': 'package',
                'id': package.id,
                'name': package.name,
                'price': float(package.discounted_price),
                'original_price': float(package.price_per_person),
                'duration': package.duration_days,
                'includes': package.includes[:50]
            })

    return JsonResponse({'items': items})