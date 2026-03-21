from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Destination, Flight, Hotel, Package, Review, Booking, Contact, NewsletterSubscriber


# Customize User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


# Destination Admin
@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'category', 'budget', 'price_per_day', 'is_active', 'created_at')
    list_filter = ('category', 'budget', 'is_active', 'country')
    search_fields = ('name', 'country', 'description')
    list_editable = ('is_active', 'price_per_day')
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'country', 'category', 'budget')
        }),
        ('Details', {
            'fields': ('description', 'image_url', 'price_per_day', 'is_active')
        }),
    )


# Flight Admin
@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'airline', 'from_city', 'to_city', 'departure_date', 'departure_time', 'price',
                    'available_seats', 'is_active')
    list_filter = ('airline', 'price_category', 'is_active', 'departure_date')
    search_fields = ('flight_number', 'from_city', 'to_city', 'airline')
    list_editable = ('price', 'available_seats', 'is_active')
    list_per_page = 25
    date_hierarchy = 'departure_date'

    fieldsets = (
        ('Flight Information', {
            'fields': ('airline', 'flight_number')
        }),
        ('Route', {
            'fields': ('from_city', 'to_city')
        }),
        ('Schedule', {
            'fields': ('departure_date', 'departure_time', 'arrival_time', 'duration')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'price_category', 'available_seats', 'is_active')
        }),
    )


# Hotel Admin
@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'rating', 'price_per_night', 'available_rooms', 'get_amenities_short',
                    'is_available')
    list_filter = ('location', 'price_category', 'rating', 'is_available')
    search_fields = ('name', 'location', 'amenities', 'description')
    list_editable = ('price_per_night', 'available_rooms', 'is_available')
    list_per_page = 25

    def get_amenities_short(self, obj):
        return obj.amenities[:50] + '...' if len(obj.amenities) > 50 else obj.amenities

    get_amenities_short.short_description = 'Amenities'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'rating', 'price_category')
        }),
        ('Details', {
            'fields': ('description', 'image_url', 'amenities')
        }),
        ('Pricing & Availability', {
            'fields': ('price_per_night', 'available_rooms', 'is_available')
        }),
    )


# Package Admin
@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_days', 'price_per_person', 'discount_percentage', 'discounted_price', 'is_active',
                    'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'includes')
    list_editable = ('price_per_person', 'discount_percentage', 'is_active')
    readonly_fields = ('discounted_price',)
    list_per_page = 25

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'duration_days', 'includes')
        }),
        ('Description', {
            'fields': ('description', 'image_url')
        }),
        ('Pricing', {
            'fields': ('price_per_person', 'discount_percentage', 'discounted_price', 'is_active')
        }),
    )


# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'review_type', 'rating', 'is_approved', 'created_at', 'get_review_preview')
    list_filter = ('review_type', 'rating', 'is_approved', 'created_at')
    search_fields = ('name', 'text', 'review_type')
    list_editable = ('is_approved',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['approve_reviews', 'reject_reviews']

    def get_review_preview(self, obj):
        return obj.text[:75] + '...' if len(obj.text) > 75 else obj.text

    get_review_preview.short_description = 'Review Preview'

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} review(s) approved successfully.")

    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} review(s) rejected.")

    reject_reviews.short_description = "Reject selected reviews"

    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'name', 'review_type', 'rating')
        }),
        ('Content', {
            'fields': ('text', 'is_approved')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    readonly_fields = ('created_at',)


# Booking Admin - FIXED VERSION
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'booking_type', 'item_name', 'total_price', 'status', 'booking_date',
                    'travel_date')
    list_filter = ('booking_type', 'status', 'booking_date')  # Removed payment_status
    search_fields = ('ticket_number', 'user__username', 'item_name', 'email')
    list_editable = ('status',)
    readonly_fields = ('ticket_number', 'booking_date')
    list_per_page = 25
    date_hierarchy = 'booking_date'
    actions = ['confirm_bookings', 'cancel_bookings']  # Removed mark_paid

    def confirm_bookings(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} booking(s) confirmed.")

    confirm_bookings.short_description = "Confirm selected bookings"

    def cancel_bookings(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} booking(s) cancelled.")

    cancel_bookings.short_description = "Cancel selected bookings"

    fieldsets = (
        ('Booking Information', {
            'fields': ('ticket_number', 'user', 'booking_type', 'item_name', 'item_id')
        }),
        ('Travel Details', {
            'fields': ('travel_date', 'number_of_people', 'check_in_date', 'check_out_date')
        }),
        ('Payment', {
            'fields': ('total_price', 'status')  # Removed payment_status and payment_method
        }),
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone', 'special_requests')
        }),
    )


# Contact Admin
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at', 'get_message_preview')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_resolved',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def get_message_preview(self, obj):
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message

    get_message_preview.short_description = 'Message Preview'

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f"{updated} message(s) marked as resolved.")

    mark_as_resolved.short_description = "Mark as resolved"

    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f"{updated} message(s) marked as unresolved.")

    mark_as_unresolved.short_description = "Mark as unresolved"


# Newsletter Admin
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    list_editable = ('is_active',)
    list_per_page = 25
    date_hierarchy = 'subscribed_at'
    actions = ['activate_subscribers', 'deactivate_subscribers']

    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} subscriber(s) activated.")

    activate_subscribers.short_description = "Activate selected subscribers"

    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} subscriber(s) deactivated.")

    deactivate_subscribers.short_description = "Deactivate selected subscribers"


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize Admin Site
admin.site.site_header = "Tower Travel Tourism Administration"
admin.site.site_title = "Tower Travel Admin"
admin.site.index_title = "Welcome to Tower Travel Management System"