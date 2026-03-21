from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta


# Destination Module
class Destination(models.Model):
    CATEGORY_CHOICES = [
        ('beach', 'Beach'),
        ('mountain', 'Mountain'),
        ('city', 'City'),
        ('desert', 'Desert'),
        ('forest', 'Forest'),
    ]

    BUDGET_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    budget = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    description = models.TextField()
    image_url = models.URLField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.country}"


# Flight Module
class Flight(models.Model):
    AIRLINE_CHOICES = [
        ('emirates', 'Emirates'),
        ('qatar', 'Qatar Airways'),
        ('turkish', 'Turkish Airlines'),
        ('pia', 'PIA'),
        ('etihad', 'Etihad Airways'),
        ('air_france', 'Air France'),
    ]

    PRICE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    airline = models.CharField(max_length=50, choices=AIRLINE_CHOICES)
    flight_number = models.CharField(max_length=20)
    from_city = models.CharField(max_length=100)
    to_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    duration = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    price_category = models.CharField(max_length=20, choices=PRICE_CHOICES)
    available_seats = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.airline} {self.flight_number}: {self.from_city} → {self.to_city}"


# Hotel Module
class Hotel(models.Model):
    LOCATION_CHOICES = [
        ('paris', 'Paris'),
        ('dubai', 'Dubai'),
        ('newyork', 'New York'),
        ('london', 'London'),
        ('tokyo', 'Tokyo'),
    ]

    PRICE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    price_category = models.CharField(max_length=20, choices=PRICE_CHOICES)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    description = models.TextField()
    image_url = models.URLField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    available_rooms = models.IntegerField()
    is_available = models.BooleanField(default=True)
    amenities = models.TextField(help_text="Comma separated amenities")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"


# Package Module
class Package(models.Model):
    name = models.CharField(max_length=200)
    duration_days = models.IntegerField()
    includes = models.TextField(help_text="What's included in the package")
    description = models.TextField()
    image_url = models.URLField()
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField(default=0)
    max_people = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def discounted_price(self):
        if self.discount_percentage > 0:
            discount = (self.price_per_person * self.discount_percentage) / 100
            return self.price_per_person - discount
        return self.price_per_person

    def __str__(self):
        return self.name


# Review Module
class Review(models.Model):
    REVIEW_TYPE_CHOICES = [
        ('Destination', 'Destination'),
        ('Hotel', 'Hotel'),
        ('Flight', 'Flight'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating}★"


# Booking Module - Updated with payment fields
class Booking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('destination', 'Destination'),
        ('hotel', 'Hotel'),
        ('flight', 'Flight'),
        ('package', 'Package'),
    ]

    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('partial', 'Partially Paid'),
        ('completed', 'Payment Completed'),
        ('refunded', 'Refunded'),
        ('failed', 'Payment Failed'),
    ]

    # Basic Info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')

    # Item Details
    item_id = models.IntegerField()
    item_name = models.CharField(max_length=200)
    item_details = models.TextField(blank=True, null=True)

    # Travel Details
    travel_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    number_of_people = models.IntegerField(default=1)
    number_of_rooms = models.IntegerField(default=1, null=True, blank=True)

    # Pricing
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # PAYMENT FIELDS
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_due_date = models.DateField(blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Contact Information
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    special_requests = models.TextField(blank=True, null=True)

    # Booking Reference
    ticket_number = models.CharField(max_length=50, unique=True)

    @property
    def days_until_due(self):
        """Return days until payment is due"""
        if self.payment_due_date:
            from datetime import date
            delta = self.payment_due_date - date.today()
            return delta.days
        return 7

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.days_until_due < 0 and self.remaining_amount > 0

    @property
    def payment_progress(self):
        """Return payment progress percentage"""
        if self.total_price > 0:
            return (self.amount_paid / self.total_price) * 100
        return 0

    def __str__(self):
        return f"{self.ticket_number} - {self.user.username} - {self.item_name}"

    def save(self, *args, **kwargs):
        # Set remaining amount on save
        if not self.remaining_amount or self.remaining_amount == 0:
            self.remaining_amount = self.total_price - self.amount_paid

        # Set payment due date (7 days from booking if not set)
        if not self.payment_due_date and not self.id:
            self.payment_due_date = (datetime.now().date() + timedelta(days=7))

        # Update payment status based on amount paid
        if self.remaining_amount <= 0:
            self.payment_status = 'completed'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'

        super().save(*args, **kwargs)


# Contact Module
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']


# Newsletter Subscriber Module
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email