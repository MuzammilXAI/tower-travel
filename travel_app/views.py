from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from .models import Destination, Flight, Hotel, Package, Review, Booking, Contact, NewsletterSubscriber, \
    EmailVerification
import random
import re
from django.core.mail import send_mail
import string
from datetime import datetime, timedelta
from django.utils import timezone
import json
from django.conf import settings
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site
import uuid


def generate_ticket_number():
    """Generate unique ticket number"""
    return 'TKT-' + ''.join(random.choices(string.digits, k=8))


# ==================== USER AUTHENTICATION WITH EMAIL VERIFICATION ====================

def user_signup_view(request):
    """User signup with email verification"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'user_signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'user_signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'user_signup.html')

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long!')
            return render(request, 'user_signup.html')

        # Create user (inactive until email verification)
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False
        )

        # Create verification token
        verification = EmailVerification.objects.create(user=user)

        # Send verification email
        current_site = get_current_site(request)
        verification_link = f"{request.scheme}://{current_site.domain}/verify-email/?token={verification.token}"

        email_subject = 'Verify Your Tower Travel Account'
        email_message = f"""
Hello {username},

Thank you for signing up with Tower Travel Tourism!

Please click the link below to verify your email address and activate your account:

{verification_link}

This link will expire in 24 hours.

If you did not sign up for this account, please ignore this email.

Best regards,
Tower Travel Team
        """

        try:
            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request,
                             '✨ Verification email sent! Please check your inbox (and spam folder) to activate your account.')
            return redirect(f"/signup/?verification_sent=1")
        except Exception as e:
            user.delete()
            messages.error(request, f'Failed to send verification email. Please try again.')
            return render(request, 'user_signup.html')

    return render(request, 'user_signup.html')


def verify_email_view(request):
    """Verify user email and activate account"""
    token = request.GET.get('token')

    if not token:
        messages.error(request, 'Invalid verification link.')
        return redirect('user_login')

    try:
        verification = EmailVerification.objects.get(token=token, is_verified=False)

        if verification.is_expired():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('resend_verification')

        # Activate user account
        user = verification.user
        user.is_active = True
        user.save()

        verification.is_verified = True
        verification.save()

        messages.success(request, '✅ Email verified successfully! You can now login to your account.')
        return redirect('user_login')

    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('user_login')


def resend_verification_email(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email, is_active=False)
            verification, created = EmailVerification.objects.get_or_create(user=user)

            # Update token
            verification.token = uuid.uuid4()
            verification.created_at = timezone.now()
            verification.is_verified = False
            verification.save()

            # Resend email
            current_site = get_current_site(request)
            verification_link = f"{request.scheme}://{current_site.domain}/verify-email/?token={verification.token}"

            send_mail(
                'Resend: Verify Your Tower Travel Account',
                f"Click to verify your account: {verification_link}\n\nThis link expires in 24 hours.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            messages.success(request, '📧 Verification email resent! Please check your inbox.')
            return redirect('user_login')

        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with this email.')
        except Exception as e:
            messages.error(request, 'Error sending verification email. Please try again.')

    return render(request, 'resend_verification.html')


def user_login_view(request):
    """User login - only for regular users (not admin)"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            messages.info(request, 'Please use Admin Portal for admin access.')
            return redirect('admin_login')
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                messages.warning(request, '⚠️ Please use the Admin Portal to login.')
                return redirect('admin_login')

            if not user.is_active:
                messages.warning(request,
                                 '⚠️ Please verify your email before logging in. Check your inbox or request a new verification email.')
                return redirect('resend_verification')

            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}! ✈️')

            # Redirect to next parameter if exists
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'user_login.html')


def user_logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('user_login')


def admin_login_view(request):
    """Admin login - only for superusers (no signup page)"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_page')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            # Try with username
            user = authenticate(request, username=email, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, f'Welcome Admin, {user.username}! 👑')
            return redirect('admin_page')
        elif user is not None and not user.is_superuser:
            messages.error(request, 'Access denied. This portal is for administrators only.')
        else:
            messages.error(request, 'Invalid admin credentials. Please check your email and password.')

    return render(request, 'admin_login.html')


def admin_logout_view(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'Admin logged out successfully.')
    return redirect('admin_login')


# ==================== COMPATIBILITY VIEWS (Keep existing template links working) ====================

def login_view(request):
    """Redirect to user login - for compatibility"""
    return redirect('user_login')


def signup_view(request):
    """Redirect to user signup - for compatibility"""
    return redirect('user_signup')


def logout_view(request):
    """Redirect to user logout - for compatibility"""
    return redirect('user_logout')


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
            return redirect('user_login')

    return render(request, 'reset_password.html', {'username': username})


# ==================== USER PROFILE MANAGEMENT ====================

@login_required(login_url='user_login')
def my_profile_view(request):
    """View user profile"""
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')[:5]

    total_spent = Booking.objects.filter(
        user=user,
        payment_status='completed'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    context = {
        'user': user,
        'bookings': bookings,
        'total_bookings': Booking.objects.filter(user=user).count(),
        'total_spent': total_spent,
    }
    return render(request, 'my_profile.html', context)


@login_required(login_url='user_login')
def edit_profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Check if username already exists (excluding current user)
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, 'Username already taken!')
            return redirect('edit_profile')

        # Check if email already exists (excluding current user)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Email already registered!')
            return redirect('edit_profile')

        # Update user details
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, '✅ Profile updated successfully!')
        return redirect('my_profile')

    return render(request, 'edit_profile.html', {'user': request.user})


@login_required(login_url='user_login')
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect!')
            return redirect('change_password')

        # Check new password length
        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters long!')
            return redirect('change_password')

        # Check if passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('change_password')

        # Update password
        user.set_password(new_password)
        user.save()

        # Logout user and redirect to login
        logout(request)
        messages.success(request, '🔐 Password changed successfully! Please login with your new password.')
        return redirect('user_login')

    return render(request, 'change_password.html')


@login_required(login_url='user_login')
def delete_account_view(request):
    """Delete user account"""
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation')

        if confirmation == 'DELETE':
            user = request.user

            # Delete all related bookings
            Booking.objects.filter(user=user).delete()

            # Delete the user
            user.delete()

            messages.success(request, '🗑️ Your account has been deleted successfully.')
            return redirect('user_login')
        else:
            messages.error(request, 'Please type "DELETE" to confirm account deletion.')
            return redirect('my_profile')

    return redirect('my_profile')


# --- MODULE VIEWS ---
@login_required(login_url='user_login')
def index_view(request):
    return render(request, 'index.html')


@login_required(login_url='user_login')
def destination_view(request):
    from datetime import date
    today = date.today()

    destinations = Destination.objects.filter(is_active=True)

    search_query = request.GET.get('search', '')
    if search_query:
        destinations = destinations.filter(
            Q(name__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    category = request.GET.get('category', '')
    if category:
        destinations = destinations.filter(category=category)

    budget = request.GET.get('budget', '')
    if budget:
        destinations = destinations.filter(budget=budget)

    context = {
        'destinations': destinations,
        'today': today,
        'search_query': search_query,
        'selected_category': category,
        'selected_budget': budget,
    }
    return render(request, 'destination.html', context)


@login_required(login_url='user_login')
def flight_view(request):
    flights = Flight.objects.filter(is_active=True)

    from_city = request.GET.get('from', '')
    if from_city:
        flights = flights.filter(from_city__icontains=from_city)

    to_city = request.GET.get('to', '')
    if to_city:
        flights = flights.filter(to_city__icontains=to_city)

    date = request.GET.get('date', '')
    if date:
        flights = flights.filter(departure_date=date)

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


@login_required(login_url='user_login')
def hotel_view(request):
    hotels = Hotel.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        hotels = hotels.filter(name__icontains=search_query)

    location = request.GET.get('location', '')
    if location:
        hotels = hotels.filter(location=location)

    price = request.GET.get('price', '')
    if price:
        hotels = hotels.filter(price_category=price)

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


@login_required(login_url='user_login')
def package_view(request):
    packages = Package.objects.filter(is_active=True)
    context = {'packages': packages}
    return render(request, 'package.html', context)


@login_required(login_url='user_login')
def reviews_view(request):
    if request.method == 'POST':
        review_type = request.POST.get('review_type')
        name = request.POST.get('name')
        text = request.POST.get('text')
        rating = request.POST.get('rating')

        if name and text and rating:
            review = Review(
                user=request.user if request.user.is_authenticated else None,
                review_type=review_type,
                name=name,
                text=text,
                rating=int(rating),
            )
            try:
                review.is_approved = False
            except:
                pass
            review.save()
            messages.success(request, 'Review submitted successfully! It will be visible after approval.')
        else:
            messages.error(request, 'Please fill all fields.')
        return redirect('reviews')

    try:
        reviews = Review.objects.filter(is_approved=True).order_by('-created_at')
    except:
        reviews = Review.objects.all().order_by('-created_at')

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
    }
    return render(request, 'reviews.html', context)


# ==================== PERSONALIZED RECOMMENDATIONS API ====================
@login_required(login_url='user_login')
def personalized_recommendations_api(request):
    """API endpoint for personalized recommendations based on user behavior"""

    user = request.user
    recommendations = []

    # Get user's booking history
    user_bookings = Booking.objects.filter(user=user, status='confirmed')

    # Extract user preferences from bookings
    preferred_categories = []
    preferred_budgets = []
    preferred_locations = []
    booked_item_ids = {
        'destination': [],
        'hotel': [],
        'flight': [],
        'package': []
    }

    for booking in user_bookings:
        if booking.booking_type == 'destination':
            dest = Destination.objects.filter(id=booking.item_id).first()
            if dest:
                preferred_categories.append(dest.category)
                preferred_budgets.append(dest.budget)
                booked_item_ids['destination'].append(booking.item_id)
        elif booking.booking_type == 'hotel':
            hotel = Hotel.objects.filter(id=booking.item_id).first()
            if hotel:
                preferred_locations.append(hotel.location)
                preferred_budgets.append(hotel.price_category)
                booked_item_ids['hotel'].append(booking.item_id)
        elif booking.booking_type == 'flight':
            flight = Flight.objects.filter(id=booking.item_id).first()
            if flight:
                preferred_locations.append(flight.to_city)
                booked_item_ids['flight'].append(booking.item_id)
        elif booking.booking_type == 'package':
            package = Package.objects.filter(id=booking.item_id).first()
            if package:
                booked_item_ids['package'].append(booking.item_id)

    # Get most common preferences
    from collections import Counter
    top_category = Counter(preferred_categories).most_common(1)[0][0] if preferred_categories else None
    top_budget = Counter(preferred_budgets).most_common(1)[0][0] if preferred_budgets else None
    top_location = Counter(preferred_locations).most_common(1)[0][0] if preferred_locations else None

    # 1. Content-Based Recommendations
    if top_category:
        similar_destinations = Destination.objects.filter(
            category=top_category,
            is_active=True
        ).exclude(id__in=booked_item_ids['destination'])[:3]

        for dest in similar_destinations:
            recommendations.append({
                'type': 'destination',
                'name': dest.name,
                'country': dest.country,
                'price': float(dest.price_per_day),
                'image': dest.image_url,
                'reason': f"Based on your interest in {top_category} destinations",
                'match_percentage': 85
            })

    if top_budget:
        similar_hotels = Hotel.objects.filter(
            price_category=top_budget
        ).exclude(id__in=booked_item_ids['hotel'])[:3]

        for hotel in similar_hotels:
            recommendations.append({
                'type': 'hotel',
                'name': hotel.name,
                'location': hotel.location,
                'price': float(hotel.price_per_night),
                'rating': hotel.rating,
                'image': hotel.image_url,
                'reason': f"Matches your preferred {top_budget} budget range",
                'match_percentage': 80
            })

    if top_location:
        similar_flights = Flight.objects.filter(
            Q(to_city__icontains=top_location) | Q(from_city__icontains=top_location),
            is_active=True
        ).exclude(id__in=booked_item_ids['flight'])[:3]

        for flight in similar_flights:
            recommendations.append({
                'type': 'flight',
                'name': f"{flight.get_airline_display()} {flight.flight_number}",
                'from_city': flight.from_city,
                'to_city': flight.to_city,
                'price': float(flight.price),
                'airline': flight.get_airline_display(),
                'departure': flight.departure_time.strftime('%H:%M'),
                'arrival': flight.arrival_time.strftime('%H:%M'),
                'duration': flight.duration,
                'image': None,
                'reason': f"Flights to/from {top_location}",
                'match_percentage': 75
            })

    # 2. Collaborative Filtering
    if user_bookings.exists():
        similar_users = Booking.objects.filter(
            item_name__in=[b.item_name for b in user_bookings],
            status='confirmed'
        ).exclude(user=user).values('user').distinct()[:10]

        similar_user_ids = [u['user'] for u in similar_users]

        if similar_user_ids:
            collaborative_items = Booking.objects.filter(
                user_id__in=similar_user_ids,
                status='confirmed'
            ).exclude(
                item_name__in=[b.item_name for b in user_bookings]
            ).values('booking_type', 'item_name', 'item_id').distinct()[:5]

            for item in collaborative_items:
                if item['booking_type'] == 'destination':
                    dest = Destination.objects.filter(id=item['item_id']).first()
                    if dest and dest.id not in booked_item_ids['destination']:
                        recommendations.append({
                            'type': 'destination',
                            'name': dest.name,
                            'country': dest.country,
                            'price': float(dest.price_per_day),
                            'image': dest.image_url,
                            'reason': "Popular among travelers with similar taste",
                            'match_percentage': 90
                        })
                elif item['booking_type'] == 'hotel':
                    hotel = Hotel.objects.filter(id=item['item_id']).first()
                    if hotel and hotel.id not in booked_item_ids['hotel']:
                        recommendations.append({
                            'type': 'hotel',
                            'name': hotel.name,
                            'location': hotel.location,
                            'price': float(hotel.price_per_night),
                            'rating': hotel.rating,
                            'image': hotel.image_url,
                            'reason': "Recommended by travelers like you",
                            'match_percentage': 88
                        })
                elif item['booking_type'] == 'package':
                    package = Package.objects.filter(id=item['item_id']).first()
                    if package and package.id not in booked_item_ids['package']:
                        recommendations.append({
                            'type': 'package',
                            'name': package.name,
                            'price': float(package.discounted_price),
                            'duration': package.duration_days,
                            'includes': package.includes[:50],
                            'image': package.image_url,
                            'reason': "Trending among similar travelers",
                            'match_percentage': 85
                        })

    # 3. Popular items (fallback)
    if len(recommendations) < 5:
        all_destinations = Destination.objects.filter(is_active=True)
        popular_list = []
        for dest in all_destinations:
            booking_count = Booking.objects.filter(booking_type='destination', item_id=dest.id,
                                                   status='confirmed').count()
            popular_list.append((dest, booking_count))
        popular_list.sort(key=lambda x: x[1], reverse=True)
        popular_destinations = [item[0] for item in popular_list[:3]]

        for dest in popular_destinations:
            if dest.id not in booked_item_ids['destination']:
                recommendations.append({
                    'type': 'destination',
                    'name': dest.name,
                    'country': dest.country,
                    'price': float(dest.price_per_day),
                    'image': dest.image_url,
                    'reason': "Trending destination this month!",
                    'match_percentage': 95
                })

    # Remove duplicates
    seen_names = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec['name'] not in seen_names:
            seen_names.add(rec['name'])
            unique_recommendations.append(rec)

    # Sort by match percentage
    unique_recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)
    unique_recommendations = unique_recommendations[:8]

    return JsonResponse({
        'success': True,
        'recommendations': unique_recommendations,
        'has_history': user_bookings.exists(),
        'total_recommendations': len(unique_recommendations)
    })


# --- ENHANCED BOOKING VIEWS ---
@login_required(login_url='user_login')
def book_item(request):
    """Enhanced booking function for all item types with payment fields"""
    if request.method == 'POST':
        try:
            booking_type = request.POST.get('booking_type')
            item_id = request.POST.get('item_id')
            travel_date = request.POST.get('travel_date')
            people = int(request.POST.get('people', 1))

            full_name = request.POST.get('full_name', request.user.get_full_name() or request.user.username)
            email = request.POST.get('email', request.user.email)
            phone = request.POST.get('phone', '')
            special_requests = request.POST.get('special_requests', '')

            item_name = ""
            price_per_unit = 0
            item_details = ""
            return_date = None
            number_of_rooms = 1

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

            if booking_type == 'hotel':
                from datetime import datetime
                check_in_date = datetime.strptime(travel_date, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(return_date, '%Y-%m-%d').date() if return_date else check_in_date
                nights = (check_out_date - check_in_date).days
                if nights <= 0:
                    nights = 1
                total_price = price_per_unit * number_of_rooms * nights
            else:
                total_price = price_per_unit * people

            ticket_number = generate_ticket_number()

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
                status='confirmed',
                payment_status='pending',
                amount_paid=0,
                remaining_amount=total_price,
                payment_due_date=timezone.now().date() + timedelta(days=7)
            )

            messages.success(request, f'✅ Booking confirmed! Your ticket number is {ticket_number}')
            messages.info(request, '⚠️ Payment is pending. Please complete payment within 7 days.')

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


@login_required(login_url='user_login')
def cancel_booking(request):
    if request.method == 'POST':
        booking_type = request.POST.get('booking_type')
        item_name = request.POST.get('item_name')
        booking_id = request.POST.get('booking_id')

        booking = Booking.objects.filter(
            user=request.user,
            id=booking_id,
            status='confirmed'
        ).first()

        if booking:
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


@login_required(login_url='user_login')
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    context = {
        'bookings': bookings,
        'active_bookings': bookings.filter(status='confirmed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
    }
    return render(request, 'my_bookings.html', context)


@login_required(login_url='user_login')
def booking_confirmation(request):
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


# ===== PAYMENT VIEWS =====
@login_required(login_url='user_login')
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    days_until_due = (booking.payment_due_date - timezone.now().date()).days if booking.payment_due_date else 7
    context = {
        'booking': booking,
        'days_until_due': days_until_due,
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
    }
    return render(request, 'payment.html', context)


@login_required(login_url='user_login')
def process_payment(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        payment_method = request.POST.get('payment_method')
        amount_str = request.POST.get('amount', str(booking.remaining_amount))

        try:
            amount = Decimal(str(amount_str))
        except:
            messages.error(request, 'Invalid payment amount')
            return redirect('payment_page', booking_id=booking.id)

        if amount <= 0:
            messages.error(request, 'Invalid payment amount')
            return redirect('payment_page', booking_id=booking.id)

        if amount > booking.remaining_amount:
            messages.error(request, f'Amount exceeds remaining balance of ${booking.remaining_amount}')
            return redirect('payment_page', booking_id=booking.id)

        try:
            transaction_id = f"TXN-{generate_ticket_number()}"
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


@login_required(login_url='user_login')
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    payment_progress = (booking.amount_paid / booking.total_price * 100) if booking.total_price > 0 else 0
    days_until_due = (booking.payment_due_date - timezone.now().date()).days if booking.payment_due_date else 7
    is_overdue = days_until_due < 0

    context = {
        'booking': booking,
        'payment_progress': payment_progress,
        'days_until_due': max(0, days_until_due),
        'is_overdue': is_overdue
    }
    return render(request, 'booking_detail.html', context)


@login_required(login_url='user_login')
def make_partial_payment(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        amount = float(request.POST.get('amount', 0))

        if amount <= 0:
            messages.error(request, 'Invalid payment amount')
        elif amount > booking.remaining_amount:
            messages.error(request, f'Amount exceeds remaining balance of ${booking.remaining_amount}')
        else:
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


# ==================== ADMIN PANEL VIEWS ====================
@staff_member_required(login_url='admin_login')
def admin_page_view(request):
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    new_users_month = User.objects.filter(date_joined__date__gte=month_ago).count()

    # Destination Statistics
    total_destinations = Destination.objects.count()
    active_destinations = Destination.objects.filter(is_active=True).count()
    inactive_destinations = Destination.objects.filter(is_active=False).count()
    destinations_by_category = Destination.objects.values('category').annotate(count=Count('id')).order_by('category')
    destinations_by_budget = Destination.objects.values('budget').annotate(count=Count('id')).order_by('budget')
    popular_destinations = Booking.objects.filter(booking_type='destination').values('item_name').annotate(
        bookings=Count('id')).order_by('-bookings')[:5]

    # Hotel Statistics
    total_hotels = Hotel.objects.count()
    available_hotels = Hotel.objects.filter(available_rooms__gt=0).count()
    fully_booked_hotels = Hotel.objects.filter(available_rooms=0).count()
    hotels_by_location = Hotel.objects.values('location').annotate(count=Count('id')).order_by('location')
    hotels_by_rating = Hotel.objects.values('rating').annotate(count=Count('id')).order_by('rating')
    hotels_by_price = Hotel.objects.values('price_category').annotate(count=Count('id')).order_by('price_category')
    total_rooms_available = Hotel.objects.aggregate(Sum('available_rooms'))['available_rooms__sum'] or 0
    popular_hotels = Booking.objects.filter(booking_type='hotel').values('item_name').annotate(
        bookings=Count('id')).order_by('-bookings')[:5]

    # Flight Statistics
    total_flights = Flight.objects.count()
    active_flights = Flight.objects.filter(is_active=True).count()
    inactive_flights = Flight.objects.filter(is_active=False).count()
    upcoming_flights = Flight.objects.filter(departure_date__gte=today, departure_date__lte=today + timedelta(days=7),
                                             is_active=True).count()
    flights_by_airline = Flight.objects.values('airline').annotate(count=Count('id')).order_by('airline')
    flights_by_price = Flight.objects.values('price_category').annotate(count=Count('id')).order_by('price_category')
    total_seats_available = Flight.objects.aggregate(Sum('available_seats'))['available_seats__sum'] or 0
    popular_flights = Booking.objects.filter(booking_type='flight').values('item_name').annotate(
        bookings=Count('id')).order_by('-bookings')[:5]

    # Package Statistics
    total_packages = Package.objects.count()
    active_packages = Package.objects.filter(is_active=True).count()
    inactive_packages = Package.objects.filter(is_active=False).count()
    packages_with_discount = Package.objects.filter(discount_percentage__gt=0).count()
    avg_package_price = Package.objects.aggregate(Avg('price_per_person'))['price_per_person__avg'] or 0
    short_packages = Package.objects.filter(duration_days__lte=3).count()
    medium_packages = Package.objects.filter(duration_days__gte=4, duration_days__lte=7).count()
    long_packages = Package.objects.filter(duration_days__gt=7).count()
    popular_packages = Booking.objects.filter(booking_type='package').values('item_name').annotate(
        bookings=Count('id')).order_by('-bookings')[:5]

    # Booking Statistics
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    destination_bookings = Booking.objects.filter(booking_type='destination').count()
    hotel_bookings = Booking.objects.filter(booking_type='hotel').count()
    flight_bookings = Booking.objects.filter(booking_type='flight').count()
    package_bookings = Booking.objects.filter(booking_type='package').count()
    bookings_today = Booking.objects.filter(booking_date__date=today).count()
    bookings_week = Booking.objects.filter(booking_date__date__gte=week_ago).count()
    bookings_month = Booking.objects.filter(booking_date__date__gte=month_ago).count()

    # Revenue Statistics
    total_revenue = Booking.objects.filter(status='confirmed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_today = Booking.objects.filter(status='confirmed', booking_date__date=today).aggregate(Sum('total_price'))[
                        'total_price__sum'] or 0
    revenue_week = \
        Booking.objects.filter(status='confirmed', booking_date__date__gte=week_ago).aggregate(Sum('total_price'))[
            'total_price__sum'] or 0
    revenue_month = \
        Booking.objects.filter(status='confirmed', booking_date__date__gte=month_ago).aggregate(Sum('total_price'))[
            'total_price__sum'] or 0

    # Review Statistics
    total_reviews = Review.objects.count()
    approved_reviews = Review.objects.filter(is_approved=True).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    avg_rating = Review.objects.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0
    reviews_by_rating = Review.objects.values('rating').annotate(count=Count('id')).order_by('rating')

    # Contact Statistics
    total_contacts = Contact.objects.count()
    resolved_contacts = Contact.objects.filter(is_resolved=True).count()
    unresolved_contacts = Contact.objects.filter(is_resolved=False).count()

    # Newsletter Statistics
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    inactive_subscribers = NewsletterSubscriber.objects.filter(is_active=False).count()

    # Recent Activity
    recent_bookings = Booking.objects.select_related('user').order_by('-booking_date')[:10]
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    recent_reviews = Review.objects.all().order_by('-created_at')[:10]
    recent_contacts = Contact.objects.all().order_by('-created_at')[:10]

    # All Data
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
        'total_users': total_users, 'active_users': active_users, 'inactive_users': inactive_users,
        'staff_users': staff_users, 'superusers': superusers, 'new_users_today': new_users_today,
        'new_users_week': new_users_week, 'new_users_month': new_users_month, 'all_users': all_users,
        'total_destinations': total_destinations, 'active_destinations': active_destinations,
        'inactive_destinations': inactive_destinations, 'destinations_by_category': destinations_by_category,
        'destinations_by_budget': destinations_by_budget, 'popular_destinations': popular_destinations,
        'all_destinations': all_destinations, 'total_hotels': total_hotels, 'available_hotels': available_hotels,
        'fully_booked_hotels': fully_booked_hotels, 'hotels_by_location': hotels_by_location,
        'hotels_by_rating': hotels_by_rating, 'hotels_by_price': hotels_by_price,
        'total_rooms_available': total_rooms_available, 'popular_hotels': popular_hotels, 'all_hotels': all_hotels,
        'total_flights': total_flights, 'active_flights': active_flights, 'inactive_flights': inactive_flights,
        'upcoming_flights': upcoming_flights, 'flights_by_airline': flights_by_airline,
        'flights_by_price': flights_by_price, 'total_seats_available': total_seats_available,
        'popular_flights': popular_flights, 'all_flights': all_flights, 'total_packages': total_packages,
        'active_packages': active_packages, 'inactive_packages': inactive_packages,
        'packages_with_discount': packages_with_discount, 'avg_package_price': avg_package_price,
        'short_packages': short_packages, 'medium_packages': medium_packages, 'long_packages': long_packages,
        'popular_packages': popular_packages, 'all_packages': all_packages, 'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings, 'cancelled_bookings': cancelled_bookings,
        'pending_bookings': pending_bookings, 'destination_bookings': destination_bookings,
        'hotel_bookings': hotel_bookings, 'flight_bookings': flight_bookings, 'package_bookings': package_bookings,
        'bookings_today': bookings_today, 'bookings_week': bookings_week, 'bookings_month': bookings_month,
        'all_bookings': all_bookings, 'total_revenue': total_revenue, 'revenue_today': revenue_today,
        'revenue_week': revenue_week, 'revenue_month': revenue_month, 'total_reviews': total_reviews,
        'approved_reviews': approved_reviews, 'pending_reviews': pending_reviews, 'avg_rating': avg_rating,
        'reviews_by_rating': reviews_by_rating, 'all_reviews': all_reviews, 'total_contacts': total_contacts,
        'resolved_contacts': resolved_contacts, 'unresolved_contacts': unresolved_contacts,
        'all_contacts': all_contacts, 'total_subscribers': total_subscribers, 'active_subscribers': active_subscribers,
        'inactive_subscribers': inactive_subscribers, 'all_subscribers': all_subscribers,
        'recent_bookings': recent_bookings, 'recent_users': recent_users, 'recent_reviews': recent_reviews,
        'recent_contacts': recent_contacts,
    }

    return render(request, 'admin.html', context)


# ===== USER MANAGEMENT =====
@staff_member_required(login_url='admin_login')
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
            User.objects.create_user(username=username, email=email, password=password, is_active=True)
            messages.success(request, f'User {username} created successfully')
    return redirect('admin_page')


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
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
@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_delete_destination(request, dest_id):
    try:
        dest = Destination.objects.get(id=dest_id)
        dest.delete()
        messages.success(request, 'Destination deleted successfully')
    except Destination.DoesNotExist:
        messages.error(request, 'Destination not found')
    return redirect('admin_page')


# ===== HOTEL MANAGEMENT =====
@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_delete_hotel(request, hotel_id):
    try:
        hotel = Hotel.objects.get(id=hotel_id)
        hotel.delete()
        messages.success(request, 'Hotel deleted successfully')
    except Hotel.DoesNotExist:
        messages.error(request, 'Hotel not found')
    return redirect('admin_page')


# ===== FLIGHT MANAGEMENT =====
@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_delete_flight(request, flight_id):
    try:
        flight = Flight.objects.get(id=flight_id)
        flight.delete()
        messages.success(request, 'Flight deleted successfully')
    except Flight.DoesNotExist:
        messages.error(request, 'Flight not found')
    return redirect('admin_page')


# ===== PACKAGE MANAGEMENT =====
@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_delete_package(request, package_id):
    try:
        package = Package.objects.get(id=package_id)
        package.delete()
        messages.success(request, 'Package deleted successfully')
    except Package.DoesNotExist:
        messages.error(request, 'Package not found')
    return redirect('admin_page')


# ===== REVIEW MANAGEMENT =====
@staff_member_required(login_url='admin_login')
def admin_approve_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        review.is_approved = True
        review.save()
        messages.success(request, 'Review approved successfully')
    except Review.DoesNotExist:
        messages.error(request, 'Review not found')
    return redirect('admin_page')


@staff_member_required(login_url='admin_login')
def admin_delete_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
        review.delete()
        messages.success(request, 'Review deleted successfully')
    except Review.DoesNotExist:
        messages.error(request, 'Review not found')
    return redirect('admin_page')


# ===== CONTACT MANAGEMENT =====
@staff_member_required(login_url='admin_login')
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
@staff_member_required(login_url='admin_login')
def admin_view_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'view_booking.html', {'booking': booking})


@staff_member_required(login_url='admin_login')
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


@staff_member_required(login_url='admin_login')
def admin_delete_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.delete()
        messages.success(request, 'Booking deleted successfully')
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found')
    return redirect('admin_page')


# ==================== AI MODULE FUNCTIONS ====================
def ai_recommendations_api(request):
    rec_type = request.GET.get('type', 'all')
    budget = request.GET.get('budget', '')
    search = request.GET.get('search', '')
    recommendations = []

    if rec_type == 'all' or rec_type == 'destination':
        destinations = Destination.objects.filter(is_active=True)
        if budget:
            destinations = destinations.filter(budget=budget)
        if search:
            destinations = destinations.filter(Q(name__icontains=search) | Q(country__icontains=search))
        for dest in destinations[:10]:
            recommendations.append({
                'type': 'destination', 'name': dest.name, 'country': dest.country,
                'category': dest.category, 'budget': dest.budget, 'price': float(dest.price_per_day),
                'description': dest.description[:100], 'image': dest.image_url,
                'weather': get_weather_for_country(dest.country), 'rating': 4.5,
            })

    if rec_type == 'all' or rec_type == 'hotel':
        hotels = Hotel.objects.all()
        if budget:
            hotels = hotels.filter(price_category=budget)
        if search:
            hotels = hotels.filter(name__icontains=search)
        for hotel in hotels[:10]:
            recommendations.append({
                'type': 'hotel', 'name': hotel.name, 'location': hotel.location,
                'budget': hotel.price_category, 'price': float(hotel.price_per_night),
                'rating': hotel.rating, 'amenities': hotel.amenities[:50], 'image': hotel.image_url,
            })

    if rec_type == 'all' or rec_type == 'flight':
        flights = Flight.objects.filter(is_active=True)
        if budget:
            flights = flights.filter(price_category=budget)
        if search:
            flights = flights.filter(
                Q(airline__icontains=search) | Q(from_city__icontains=search) | Q(to_city__icontains=search))
        for flight in flights[:10]:
            recommendations.append({
                'type': 'flight', 'airline': flight.get_airline_display(), 'flight_number': flight.flight_number,
                'from': flight.from_city, 'to': flight.to_city, 'budget': flight.price_category,
                'price': float(flight.price), 'duration': flight.duration,
                'departure': flight.departure_time.strftime('%H:%M'), 'arrival': flight.arrival_time.strftime('%H:%M'),
                'weather': get_weather_for_city(flight.to_city),
            })

    if rec_type == 'all' or rec_type == 'package':
        packages = Package.objects.filter(is_active=True)
        if search:
            packages = packages.filter(name__icontains=search)
        for package in packages[:10]:
            recommendations.append({
                'type': 'package', 'name': package.name, 'duration': package.duration_days,
                'price': float(package.discounted_price), 'original_price': float(package.price_per_person),
                'discount': package.discount_percentage, 'includes': package.includes[:50], 'image': package.image_url,
            })

    if budget:
        recommendations.sort(key=lambda x: x.get('price', 0))

    return JsonResponse({'recommendations': recommendations[:20]})


def ai_chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').lower()
            response = generate_ai_response(message, request.user if request.user.is_authenticated else None, request)
            return JsonResponse({'response': response})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def generate_ai_response(message, user, request=None):
    message_lower = message.lower()
    import re

    if any(word in message_lower for word in
           ['book', 'reserve', 'booking', 'want to book', 'i want to book', 'book now']):
        if 'destination' in message_lower or 'place' in message_lower or 'beach' in message_lower or 'mountain' in message_lower or 'city' in message_lower:
            destinations = Destination.objects.filter(is_active=True)[:5]
            response = "🌍 **Available Destinations to Book:**\n\n"
            for dest in destinations:
                response += f"• **{dest.name}** ({dest.country}) - ${dest.price_per_day}/day - {dest.category}\n"
            response += "\nTo book, reply with: \"Book [destination name] on [YYYY-MM-DD] for [number] people\"\n"
            response += "Example: \"Book Beach Paradise on 2025-06-15 for 2 people\""
            return response
        elif 'hotel' in message_lower or 'stay' in message_lower or 'room' in message_lower:
            hotels = Hotel.objects.filter(available_rooms__gt=0)[:5]
            response = "🏨 **Available Hotels to Book:**\n\n"
            for hotel in hotels:
                response += f"• **{hotel.name}** ({hotel.location}) - ${hotel.price_per_night}/night ⭐ {hotel.rating}★\n"
                response += f"  📍 {hotel.amenities[:50]}...\n"
            response += "\nTo book, reply with: \"Book [hotel name] from [check-in] to [check-out] for [rooms] rooms\"\n"
            response += "Example: \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\""
            return response
        elif 'flight' in message_lower or 'fly' in message_lower or 'airline' in message_lower:
            flights = Flight.objects.filter(is_active=True, available_seats__gt=0)[:5]
            response = "✈️ **Available Flights to Book:**\n\n"
            for flight in flights:
                response += f"• **{flight.get_airline_display()}** {flight.flight_number}: {flight.from_city} → {flight.to_city}\n"
                response += f"  🕐 {flight.departure_time} | 💰 ${flight.price} | {flight.available_seats} seats left\n"
            response += "\nTo book, reply with: \"Book [airline/flight] on [date] for [number] passengers\"\n"
            response += "Example: \"Book Emirates EK001 on 2025-06-15 for 2 passengers\""
            return response
        elif 'package' in message_lower or 'tour' in message_lower or 'deal' in message_lower:
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

    if 'book' in message_lower and ('destination' in message_lower or 'place' in message_lower):
        for dest in Destination.objects.filter(is_active=True):
            if dest.name.lower() in message_lower:
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', message)
                if date_match:
                    travel_date = date_match.group()
                    people_match = re.search(r'(\d+)\s*people', message_lower) or re.search(r'for\s*(\d+)',
                                                                                            message_lower)
                    people = int(people_match.group(1)) if people_match else 2
                    total_price = float(dest.price_per_day) * people
                    if request:
                        request.session['pending_booking'] = {
                            'type': 'destination', 'item_id': dest.id, 'item_name': dest.name,
                            'country': dest.country, 'travel_date': travel_date, 'people': people,
                            'price_per_day': float(dest.price_per_day), 'total_price': total_price
                        }
                    return f"🌟 **Booking Summary:**\n\n📍 Destination: {dest.name} ({dest.country})\n📅 Travel Date: {travel_date}\n👥 People: {people}\n💰 Price: ${dest.price_per_day}/day\n💰 Total: ${total_price}\n\n✅ **Confirm this booking?** Reply with \"CONFIRM\" or \"YES\" to proceed."
                else:
                    return f"📅 Please provide a travel date in YYYY-MM-DD format.\n\nExample: \"Book {dest.name} on 2025-06-15 for 2 people\""
        return "❌ Destination not found. Please check the name and try again.\n\nAvailable destinations:\n" + "\n".join(
            [f"• {d.name} ({d.country})" for d in Destination.objects.filter(is_active=True)[:5]])

    if message_lower in ['confirm', 'yes', 'confirm booking', 'yes book', 'confirm', 'yes', 'confirm it', 'book it']:
        if request and request.session.get('pending_booking'):
            pending = request.session.get('pending_booking')
            try:
                if pending['type'] == 'destination':
                    dest = Destination.objects.get(id=pending['item_id'])
                    booking = Booking.objects.create(
                        user=user, booking_type='destination', item_id=pending['item_id'],
                        item_name=pending['item_name'],
                        item_details=f"Destination: {pending['item_name']}, Country: {pending.get('country', 'N/A')}",
                        travel_date=pending['travel_date'], number_of_people=pending['people'],
                        price_per_unit=pending['price_per_day'], total_price=pending['total_price'],
                        full_name=user.get_full_name() or user.username if user else pending['item_name'],
                        email=user.email if user else '',
                        ticket_number=generate_ticket_number(), status='confirmed',
                        payment_status='pending', amount_paid=0, remaining_amount=pending['total_price'],
                        payment_due_date=timezone.now().date() + timedelta(days=7)
                    )
                del request.session['pending_booking']
                return f"✅ **Booking Confirmed!** 🎉\n\n📋 Booking Details:\n• Ticket Number: {booking.ticket_number}\n• Item: {booking.item_name}\n• Total Amount: ${booking.total_price}\n• Payment Due: {booking.payment_due_date.strftime('%B %d, %Y')}\n\n💰 **Payment Status:** {booking.get_payment_status_display()}\n💳 Please complete payment within 7 days to confirm your booking.\n\nThank you for choosing Tower Travel! 🌟"
            except Exception as e:
                return f"❌ Sorry, there was an error processing your booking: {str(e)}"
        else:
            return "✨ Please provide the booking details first. Tell me what you'd like to book (destination, hotel, flight, or package)."

    cheapest_dest = Destination.objects.filter(is_active=True).order_by('price_per_day').first()
    cheapest_hotel = Hotel.objects.all().order_by('price_per_night').first()
    cheapest_flight = Flight.objects.filter(is_active=True).order_by('price').first()

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

    return "🌟 **Welcome to Tower Travel AI Assistant!**\n\nI can help you **BOOK** travel options and find the best deals.\n\n**Try these commands:**\n• 🏖️ \"Book Beach Paradise on 2025-06-15 for 2 people\"\n• 🏨 \"Book Grand Paris Hotel from 2025-06-15 to 2025-06-18 for 2 rooms\"\n• ✈️ \"Find cheap flights to London\"\n• 🎒 \"Show me family packages\"\n\nWhat would you like to book?"


def get_weather_for_country(country):
    weather_data = {
        'Maldives': 'Sunny, 28°C ☀️', 'Switzerland': 'Cool, 15°C ⛅', 'USA': 'Moderate, 22°C 🌤️',
        'Japan': 'Mild, 20°C 🌸', 'UAE': 'Hot, 32°C 🔥', 'France': 'Mild, 18°C 🌹',
        'Thailand': 'Warm, 30°C ☀️', 'Italy': 'Pleasant, 24°C 🍝', 'UK': 'Cloudy, 18°C ☁️',
        'Canada': 'Cool, 16°C 🍁',
    }
    return weather_data.get(country, 'Pleasant weather, 22°C 🌤️')


def get_weather_for_city(city):
    weather_data = {
        'Dubai': 'Sunny, 32°C ☀️', 'London': 'Cloudy, 18°C ☁️', 'Paris': 'Mild, 20°C 🌹',
        'New York': 'Moderate, 22°C 🗽', 'Tokyo': 'Mild, 20°C 🌸', 'Karachi': 'Warm, 28°C 🌊',
        'Istanbul': 'Pleasant, 24°C 🕌', 'Rome': 'Sunny, 25°C 🏛️', 'Bangkok': 'Hot, 32°C 🍜',
        'Sydney': 'Sunny, 24°C 🏖️',
    }
    return weather_data.get(city, 'Pleasant weather, 22°C 🌤️')


# ==================== AI HELPER FUNCTIONS ====================

@csrf_exempt
def ai_travel_tip_api(request):
    """API endpoint for AI travel tips"""
    tip = get_ai_travel_tip()
    return JsonResponse({'tip': tip})


def get_ai_travel_tip():
    """Generate AI travel tip"""
    tips = [
        "🌍 Pack light and layer your clothing for different weather conditions!",
        "📱 Download offline maps before your trip to navigate without internet.",
        "💊 Always carry a small first-aid kit with essential medications.",
        "💱 Notify your bank about travel plans to avoid card blocks.",
        "📸 Learn a few local phrases - locals appreciate the effort!",
        "🎒 Use packing cubes to organize your luggage efficiently.",
        "🔌 Bring a universal power adapter for international travel.",
        "📄 Keep digital and physical copies of important documents.",
        "💧 Stay hydrated and drink bottled water in unfamiliar places.",
        "🚶 Explore local markets for authentic experiences and souvenirs.",
        "📷 Take photos of your luggage before checking in for insurance purposes.",
        "💳 Carry multiple payment methods (cash, cards, digital wallets).",
        "🔋 Bring a portable power bank for your devices.",
        "🧴 Pack sunscreen and insect repellent for tropical destinations.",
        "📞 Save local emergency numbers on your phone."
    ]
    return random.choice(tips)


@csrf_exempt
def ai_destination_summary_api(request, destination_id):
    """Get AI summary for a destination"""
    try:
        destination = Destination.objects.get(id=destination_id)

        summary = f"✨ {destination.name} is a {destination.category} destination in {destination.country}. "
        weather = get_weather_for_country(destination.country)
        summary += f"Current weather: {weather}. "

        if destination.budget == 'budget':
            summary += f"💰 This is a budget-friendly destination with prices starting from ${destination.price_per_day}/day. "
        elif destination.budget == 'moderate':
            summary += f"💵 Moderate budget destination with prices around ${destination.price_per_day}/day. "
        else:
            summary += f"💎 Luxury destination with premium experiences from ${destination.price_per_day}/day. "

        if destination.category == 'beach':
            summary += f"🏖️ Perfect for beach lovers and water activities! "
        elif destination.category == 'mountain':
            summary += f"⛰️ Ideal for adventure seekers and nature enthusiasts! "
        elif destination.category == 'city':
            summary += f"🌆 Great for culture, shopping, and urban exploration! "
        elif destination.category == 'historical':
            summary += f"🏛️ Rich in history and cultural heritage! "

        return JsonResponse({
            'summary': summary,
            'sentiment': 'POSITIVE',
            'confidence': 0.85,
            'weather': weather,
            'budget': destination.budget,
            'category': destination.category
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@csrf_exempt
def ai_sentiment_analysis_api(request):
    """Analyze sentiment of user review"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            review_text = data.get('review', '')

            positive_words = ['good', 'great', 'amazing', 'excellent', 'wonderful', 'fantastic', 'beautiful', 'love',
                              'enjoyed', 'perfect']
            negative_words = ['bad', 'poor', 'terrible', 'awful', 'disappointing', 'hate', 'worst', 'waste', 'boring',
                              'overpriced']

            text_lower = review_text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            if positive_count > negative_count:
                sentiment = 'POSITIVE'
                confidence = min(0.7 + (positive_count * 0.05), 0.95)
            elif negative_count > positive_count:
                sentiment = 'NEGATIVE'
                confidence = min(0.7 + (negative_count * 0.05), 0.95)
            else:
                sentiment = 'NEUTRAL'
                confidence = 0.6

            return JsonResponse({
                'sentiment': sentiment,
                'confidence': confidence,
                'is_positive': sentiment == 'POSITIVE'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_personalized_recommendations_api(request):
    """Get AI-powered personalized recommendations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            preferences = data.get('preferences', '')
            budget = data.get('budget', '')

            preferences_lower = preferences.lower()
            recommendations = []

            destinations = Destination.objects.filter(is_active=True)

            for dest in destinations:
                score = 0
                match_reasons = []

                if dest.category in preferences_lower:
                    score += 3
                    match_reasons.append(f"Matches your interest in {dest.category}")

                if budget and dest.budget == budget:
                    score += 2
                    match_reasons.append(f"Fits your {budget} budget")

                if dest.country.lower() in preferences_lower:
                    score += 2
                    match_reasons.append(f"Matches interest in {dest.country}")

                if score > 0:
                    recommendations.append({
                        'type': 'destination',
                        'name': dest.name,
                        'country': dest.country,
                        'category': dest.category,
                        'budget': dest.budget,
                        'price': float(dest.price_per_day),
                        'score': score,
                        'reasons': match_reasons[:3],
                        'description': dest.description[:100]
                    })

            recommendations.sort(key=lambda x: x['score'], reverse=True)

            if recommendations:
                top_dest = recommendations[0]
                recommendation_text = f"🌟 Based on your interest in '{preferences}', I highly recommend **{top_dest['name']}**! "
                recommendation_text += f"This {top_dest['category']} destination in {top_dest['country']} is perfect because:\n"
                for reason in top_dest['reasons'][:2]:
                    recommendation_text += f"• {reason}\n"
                recommendation_text += f"💰 Prices start from ${top_dest['price']}/day."
            else:
                recommendation_text = f"✨ Based on '{preferences}', I suggest exploring our popular destinations like Paris, Dubai, and Tokyo. Each offers unique experiences! Would you like specific recommendations?"

            return JsonResponse({
                'recommendations': recommendations[:5],
                'recommendation_text': recommendation_text,
                'total_matches': len(recommendations)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_generate_itinerary_api(request):
    """Generate AI-powered travel itinerary"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            destination = data.get('destination', 'Paris')
            days = int(data.get('days', 3))
            interests = data.get('interests', ['sightseeing', 'food'])

            try:
                dest_obj = Destination.objects.filter(name__icontains=destination).first()
                if dest_obj:
                    country = dest_obj.country
                else:
                    country = "the destination"
            except:
                country = "the destination"

            itinerary = {
                'destination': destination,
                'country': country,
                'duration': days,
                'daily_plan': []
            }

            activities = {
                'sightseeing': ['Visit famous landmarks', 'Explore historical sites', 'Take a city tour',
                                'Visit museums'],
                'food': ['Try local cuisine', 'Visit food markets', 'Take a cooking class', 'Fine dining experience'],
                'culture': ['Visit cultural centers', 'Attend local festivals', 'Explore art galleries',
                            'Traditional performances'],
                'adventure': ['Hiking', 'Water sports', 'Outdoor activities', 'Adventure parks'],
                'relaxation': ['Spa day', 'Beach time', 'Nature walks', 'Wellness activities']
            }

            for day in range(1, days + 1):
                daily_activities = []
                for interest in interests:
                    if interest in activities:
                        activity = random.choice(activities[interest])
                        daily_activities.append(activity)
                    else:
                        daily_activities.append(f"Explore {destination} {interest} experiences")

                if day == 1:
                    daily_activities.append(f"Arrival and check-in at your accommodation in {destination}")
                elif day == days:
                    daily_activities.append(f"Last day shopping and departure from {destination}")

                itinerary['daily_plan'].append({
                    'day': day,
                    'activities': daily_activities[:4],
                    'tips': f"Day {day} Tip: " + random.choice([
                        "Start early to avoid crowds",
                        "Book popular attractions in advance",
                        "Stay hydrated and wear comfortable shoes",
                        "Take lots of photos to capture memories",
                        "Try local restaurants for authentic experience"
                    ])
                })

            itinerary['weather'] = get_weather_for_country(country)
            budget_estimate = f"💰 Estimated budget: ${random.randint(100, 300) * days} for {days} days (including accommodation and activities)"
            itinerary['budget_estimate'] = budget_estimate

            return JsonResponse(itinerary)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_compare_destinations_api(request):
    """Compare two destinations using AI"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dest1_name = data.get('destination1', '')
            dest2_name = data.get('destination2', '')

            dest1 = Destination.objects.filter(name__icontains=dest1_name).first()
            dest2 = Destination.objects.filter(name__icontains=dest2_name).first()

            if not dest1 or not dest2:
                return JsonResponse({'error': 'One or both destinations not found'}, status=404)

            comparison = {
                'destination1': {
                    'name': dest1.name,
                    'country': dest1.country,
                    'category': dest1.category,
                    'budget': dest1.budget,
                    'price': float(dest1.price_per_day),
                    'weather': get_weather_for_country(dest1.country)
                },
                'destination2': {
                    'name': dest2.name,
                    'country': dest2.country,
                    'category': dest2.category,
                    'budget': dest2.budget,
                    'price': float(dest2.price_per_day),
                    'weather': get_weather_for_country(dest2.country)
                }
            }

            if dest1.price_per_day < dest2.price_per_day:
                price_advice = f"{dest1.name} is more budget-friendly (${dest1.price_per_day}/day vs ${dest2.price_per_day}/day)"
            else:
                price_advice = f"{dest2.name} is more budget-friendly (${dest2.price_per_day}/day vs ${dest1.price_per_day}/day)"

            verdict = f"🏆 **Comparison Verdict:**\n\n"
            verdict += f"• **Best for Budget:** {price_advice}\n"
            verdict += f"• **Best for {dest1.category}:** {dest1.name}\n"
            verdict += f"• **Best for {dest2.category}:** {dest2.name}\n\n"
            verdict += f"✨ **Recommendation:** "

            if dest1.category == dest2.category:
                verdict += f"Both destinations offer excellent {dest1.category} experiences. Consider your budget and travel preferences."
            elif 'beach' in [dest1.category, dest2.category]:
                verdict += f"If you prefer beach vacations, choose {dest1.name if dest1.category == 'beach' else dest2.name}."
            else:
                verdict += f"Your choice depends on whether you prefer {dest1.category} experiences in {dest1.name} or {dest2.category} experiences in {dest2.name}."

            comparison['verdict'] = verdict

            return JsonResponse(comparison)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_flight_deal_analysis_api(request):
    """Analyze flight deal quality"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            price = float(data.get('price', 0))
            destination = data.get('destination', '')
            season = data.get('season', 'summer')

            if price < 300:
                rating = "Excellent Deal! 🎉"
                advice = "Book now - prices rarely get this low!"
                quality = "excellent"
            elif price < 500:
                rating = "Good Deal 👍"
                advice = "This is a reasonable price. Consider booking within the next week."
                quality = "good"
            elif price < 800:
                rating = "Fair Price 💭"
                advice = "You might find better deals by waiting or setting price alerts."
                quality = "fair"
            else:
                rating = "Expensive 💰"
                advice = "Consider waiting for a sale or looking at alternative dates."
                quality = "expensive"

            season_advice = {
                'summer': 'peak season with higher prices',
                'winter': 'popular season, book early',
                'spring': 'shoulder season, good deals available',
                'fall': 'shoulder season, great value'
            }

            season_text = season_advice.get(season.lower(), 'regular season')

            return JsonResponse({
                'rating': rating,
                'advice': advice,
                'quality': quality,
                'season_insight': f"{season.capitalize()} is {season_text} for {destination}.",
                'price_comparison': f"Average price for {destination} in {season} is ${random.randint(400, 700)}"
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_voice_command_api(request):
    """Process voice commands for travel"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command = data.get('command', '').lower()

            if 'book' in command:
                response = "✈️ I can help you book! Please tell me: destination, date, and number of people."
            elif 'flight' in command:
                response = "✈️ Looking for flights! Where would you like to fly to?"
            elif 'hotel' in command:
                response = "🏨 I'll help you find hotels. Which city and dates?"
            elif 'package' in command:
                response = "🎒 Great choice! What type of package are you interested in?"
            elif 'price' in command or 'cost' in command:
                response = "💰 Our prices vary by season. Which destination are you interested in?"
            elif 'recommend' in command:
                response = "🌟 Based on your interests, I recommend checking our top-rated destinations!"
            else:
                response = "🎤 I heard: '" + command + "'. Please speak clearly or type your request."

            return JsonResponse({
                'response': response,
                'command_processed': command,
                'success': True
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def ai_travel_insights_api(request):
    """Get AI-powered travel insights and trends"""
    insights = {
        'trending_destinations': [
            {'name': 'Dubai', 'trend': '+45%', 'reason': 'Luxury shopping and architecture'},
            {'name': 'Tokyo', 'trend': '+38%', 'reason': 'Cherry blossom season'},
            {'name': 'Paris', 'trend': '+32%', 'reason': 'Summer Olympics buzz'},
            {'name': 'Bali', 'trend': '+28%', 'reason': 'Digital nomad hotspot'},
            {'name': 'Switzerland', 'trend': '+25%', 'reason': 'Alpine adventures'}
        ],
        'best_time_to_visit': {
            'Europe': 'May-September (Summer)',
            'Asia': 'November-February (Dry season)',
            'Middle East': 'November-March (Cooler months)',
            'Americas': 'Varies by region',
            'Africa': 'June-October (Safari season)'
        },
        'booking_advice': '📅 Book flights 2-3 months in advance for best prices. Hotels: 1-2 months ahead.',
        'travel_trend': '🚀 Sustainable travel and off-season trips are becoming increasingly popular!',
        'money_saving_tip': '💡 Consider traveling during shoulder seasons (April-May or September-October) for better deals and fewer crowds.'
    }

    return JsonResponse(insights)


def ai_get_weather_api(request):
    """Get weather information for destination"""
    city = request.GET.get('city', '')
    country = request.GET.get('country', '')

    if city:
        weather = get_weather_for_city(city)
        return JsonResponse({
            'location': city,
            'weather': weather,
            'advice': get_weather_advice(weather)
        })
    elif country:
        weather = get_weather_for_country(country)
        return JsonResponse({
            'location': country,
            'weather': weather,
            'advice': get_weather_advice(weather)
        })

    return JsonResponse({'error': 'Please provide city or country'}, status=400)


def get_weather_advice(weather):
    """Get travel advice based on weather"""
    if 'Sunny' in weather or 'Hot' in weather:
        return "☀️ Perfect weather for outdoor activities! Don't forget sunscreen and stay hydrated."
    elif 'Cloudy' in weather:
        return "☁️ Good for sightseeing. Bring a light jacket just in case."
    elif 'Cool' in weather or 'Mild' in weather:
        return "🍂 Comfortable weather for exploring. Layered clothing recommended."
    elif 'Rain' in weather:
        return "🌧️ Pack an umbrella and waterproof jacket. Indoor activities recommended."
    else:
        return "🌤️ Good travel conditions. Check local forecast for updates."


# ==================== AI DEBUG ENDPOINT ====================
@csrf_exempt
def ai_debug_api(request):
    return JsonResponse({
        'ai_status': {'real_ai_enabled': False, 'api_key_available': False},
        'message': '⚠️ Using simulated AI responses'
    })


# ==================== AI STATUS ENDPOINT ====================
@csrf_exempt
def ai_status_api(request):
    """API endpoint to check AI status"""
    return JsonResponse({
        'real_ai_enabled': False,
        'api_key_available': False,
        'message': 'AI Assistant is ready to help you!'
    })