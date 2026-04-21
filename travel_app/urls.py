print("travel_app.urls loaded")
from django.urls import path
from . import views

urlpatterns = [
    # ==================== USER AUTHENTICATION ====================
    # User Login & Signup with Email Verification
    path('login/', views.user_login_view, name='user_login'),
    path('signup/', views.user_signup_view, name='user_signup'),
    path('logout/', views.user_logout_view, name='logout'),

    # Email Verification Routes
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),

    # Password Management
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:username>/', views.reset_password_view, name='reset_password'),

    # ==================== USER PROFILE MANAGEMENT ====================
    path('my-profile/', views.my_profile_view, name='my_profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('delete-account/', views.delete_account_view, name='delete_account'),

    # ==================== ADMIN AUTHENTICATION (Separate - No Signup) ====================
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # ==================== COMPATIBILITY (for existing templates) ====================
    path('accounts/login/', views.user_login_view, name='login'),
    path('accounts/signup/', views.user_signup_view, name='signup'),

    # ==================== MAIN MODULE PAGES ====================
    path('', views.index_view, name='index'),
    path('destination/', views.destination_view, name='destination'),
    path('flight/', views.flight_view, name='flight'),
    path('hotel/', views.hotel_view, name='hotel'),
    path('package/', views.package_view, name='package'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('admin-dashboard/', views.admin_page_view, name='admin_page'),
    path('admin-page/', views.admin_page_view, name='admin_page_alt'),

    # ==================== USER BOOKING MANAGEMENT ====================
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking-confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('book/', views.book_item, name='book_item'),
    path('cancel/', views.cancel_booking, name='cancel_booking'),

    # ==================== PERSONALIZED RECOMMENDATIONS API ====================
    path('api/personalized-recommendations/', views.personalized_recommendations_api,
         name='personalized_recommendations'),

    # ==================== AI MODULE ENDPOINTS ====================
    path('api/recommendations/', views.ai_recommendations_api, name='ai_recommendations'),
    path('api/chatbot/', views.ai_chatbot_api, name='ai_chatbot'),

    # ==================== HUGGING FACE AI MODULE ENDPOINTS ====================
    path('api/travel-tip/', views.ai_travel_tip_api, name='ai_travel_tip'),
    path('api/destination-summary/<int:destination_id>/', views.ai_destination_summary_api,
         name='ai_destination_summary'),
    path('api/analyze-sentiment/', views.ai_sentiment_analysis_api, name='ai_sentiment_analysis'),
    path('api/recommendations-ai/', views.ai_personalized_recommendations_api, name='ai_recommendations_ai'),
    path('api/generate-itinerary/', views.ai_generate_itinerary_api, name='ai_generate_itinerary'),
    path('api/compare-destinations/', views.ai_compare_destinations_api, name='ai_compare_destinations'),
    path('api/analyze-flight-deal/', views.ai_flight_deal_analysis_api, name='ai_analyze_flight_deal'),
    path('api/voice-command/', views.ai_voice_command_api, name='ai_voice_command'),
    path('api/travel-insights/', views.ai_travel_insights_api, name='ai_travel_insights'),
    path('api/weather/', views.ai_get_weather_api, name='ai_get_weather'),
    path('api/debug/', views.ai_debug_api, name='ai_debug'),

    # ==================== PAYMENT ROUTES ====================
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('process-payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('partial-payment/<int:booking_id>/', views.make_partial_payment, name='make_partial_payment'),

    # ==================== ADMIN USER MANAGEMENT ====================
    path('dashboard/add-user/', views.admin_add_user, name='admin_add_user'),
    path('dashboard/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('dashboard/activate-user/<int:user_id>/', views.admin_activate_user, name='admin_activate_user'),

    # ==================== ADMIN DESTINATION MANAGEMENT ====================
    path('dashboard/add-destination/', views.admin_add_destination, name='admin_add_destination'),
    path('dashboard/edit-destination/<int:dest_id>/', views.admin_edit_destination, name='admin_edit_destination'),
    path('dashboard/delete-destination/<int:dest_id>/', views.admin_delete_destination,
         name='admin_delete_destination'),

    # ==================== ADMIN HOTEL MANAGEMENT ====================
    path('dashboard/add-hotel/', views.admin_add_hotel, name='admin_add_hotel'),
    path('dashboard/edit-hotel/<int:hotel_id>/', views.admin_edit_hotel, name='admin_edit_hotel'),
    path('dashboard/delete-hotel/<int:hotel_id>/', views.admin_delete_hotel, name='admin_delete_hotel'),

    # ==================== ADMIN FLIGHT MANAGEMENT ====================
    path('dashboard/add-flight/', views.admin_add_flight, name='admin_add_flight'),
    path('dashboard/edit-flight/<int:flight_id>/', views.admin_edit_flight, name='admin_edit_flight'),
    path('dashboard/delete-flight/<int:flight_id>/', views.admin_delete_flight, name='admin_delete_flight'),

    # ==================== ADMIN PACKAGE MANAGEMENT ====================
    path('dashboard/add-package/', views.admin_add_package, name='admin_add_package'),
    path('dashboard/edit-package/<int:package_id>/', views.admin_edit_package, name='admin_edit_package'),
    path('dashboard/delete-package/<int:package_id>/', views.admin_delete_package, name='admin_delete_package'),

    # ==================== ADMIN BOOKING MANAGEMENT ====================
    path('dashboard/view-booking/<int:booking_id>/', views.admin_view_booking, name='admin_view_booking'),
    path('dashboard/delete-booking/<int:booking_id>/', views.admin_delete_booking, name='admin_delete_booking'),
    path('dashboard/update-booking-status/<int:booking_id>/', views.admin_update_booking_status,
         name='admin_update_booking_status'),

    # ==================== ADMIN REVIEW MANAGEMENT ====================
    path('dashboard/approve-review/<int:review_id>/', views.admin_approve_review, name='admin_approve_review'),
    path('dashboard/delete-review/<int:review_id>/', views.admin_delete_review, name='admin_delete_review'),

    # ==================== ADMIN CONTACT MANAGEMENT ====================
    path('dashboard/mark-resolved/<int:contact_id>/', views.admin_mark_resolved, name='admin_mark_resolved'),
]