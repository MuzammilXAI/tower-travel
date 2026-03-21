print("travel_app.urls loaded")
from django.urls import path
from . import views

urlpatterns = [
    # USER AUTH
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:username>/', views.reset_password_view, name='reset_password'),

    # MODULE PAGES
    path('', views.index_view, name='index'),
    path('destination/', views.destination_view, name='destination'),
    path('flight/', views.flight_view, name='flight'),
    path('hotel/', views.hotel_view, name='hotel'),
    path('package/', views.package_view, name='package'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('admin-dashboard/', views.admin_page_view, name='admin_page'),

    # USER BOOKING MANAGEMENT
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking-confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('book/', views.book_item, name='book_item'),
    path('cancel/', views.cancel_booking, name='cancel_booking'),

    # ===== AI MODULE ENDPOINTS =====
    path('api/recommendations/', views.ai_recommendations_api, name='ai_recommendations'),
    path('api/chatbot/', views.ai_chatbot_api, name='ai_chatbot'),

    # ===== PAYMENT ROUTES =====
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('process-payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('partial-payment/<int:booking_id>/', views.make_partial_payment, name='make_partial_payment'),

    # ADMIN USER MANAGEMENT
    path('dashboard/add-user/', views.admin_add_user, name='admin_add_user'),
    path('dashboard/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('dashboard/activate-user/<int:user_id>/', views.admin_activate_user, name='admin_activate_user'),

    # ADMIN DESTINATION MANAGEMENT
    path('dashboard/add-destination/', views.admin_add_destination, name='admin_add_destination'),
    path('dashboard/edit-destination/<int:dest_id>/', views.admin_edit_destination, name='admin_edit_destination'),
    path('dashboard/delete-destination/<int:dest_id>/', views.admin_delete_destination, name='admin_delete_destination'),

    # ADMIN HOTEL MANAGEMENT
    path('dashboard/add-hotel/', views.admin_add_hotel, name='admin_add_hotel'),
    path('dashboard/edit-hotel/<int:hotel_id>/', views.admin_edit_hotel, name='admin_edit_hotel'),
    path('dashboard/delete-hotel/<int:hotel_id>/', views.admin_delete_hotel, name='admin_delete_hotel'),

    # ADMIN FLIGHT MANAGEMENT
    path('dashboard/add-flight/', views.admin_add_flight, name='admin_add_flight'),
    path('dashboard/edit-flight/<int:flight_id>/', views.admin_edit_flight, name='admin_edit_flight'),
    path('dashboard/delete-flight/<int:flight_id>/', views.admin_delete_flight, name='admin_delete_flight'),

    # ADMIN PACKAGE MANAGEMENT
    path('dashboard/add-package/', views.admin_add_package, name='admin_add_package'),
    path('dashboard/edit-package/<int:package_id>/', views.admin_edit_package, name='admin_edit_package'),
    path('dashboard/delete-package/<int:package_id>/', views.admin_delete_package, name='admin_delete_package'),

    # ADMIN BOOKING MANAGEMENT
    path('dashboard/view-booking/<int:booking_id>/', views.admin_view_booking, name='admin_view_booking'),
    path('dashboard/delete-booking/<int:booking_id>/', views.admin_delete_booking, name='admin_delete_booking'),
    # ADD THIS MISSING LINE:
    path('dashboard/update-booking-status/<int:booking_id>/', views.admin_update_booking_status, name='admin_update_booking_status'),

    # ADMIN REVIEW MANAGEMENT
    path('dashboard/approve-review/<int:review_id>/', views.admin_approve_review, name='admin_approve_review'),
    path('dashboard/delete-review/<int:review_id>/', views.admin_delete_review, name='admin_delete_review'),

    # ADMIN CONTACT MANAGEMENT
    path('dashboard/mark-resolved/<int:contact_id>/', views.admin_mark_resolved, name='admin_mark_resolved'),
]