from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import contact
from .views import jobs
from .views import brand_guidelines
from .views import search_trends
from .views import return_success
from .views import confirm_exchange
from .views import cancel_success
from .views import product_detail, submit_review
from .views import return_policy
from .views import shipping_policy
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Existing URLs
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('categories/', views.categories, name='categories'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path("contact/", contact, name="contact"),
    
    #otp
    path('send-otp/', views.send_otp, name='send_otp'),
    path('register/', views.register, name='register'),
   


    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
     # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    #path('logout/', logout_view, name='logout'),
    path('logout/', auth_views.LogoutView.as_view(template_name='store/auth/logout.html'), name='logout'),
    path('profile/', login_required(views.profile_view), name='profile'),

    # Cart and Checkout URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),

    # Order Confirmation URL
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),

    # Razorpay Order URL
    #path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    
    # Orders List URL
    path('orders/', views.orders_list, name='orders_list'),
    
    # Footer
    path('pricing/', views.pricing, name='pricing'),
    path('jobs/', jobs, name='jobs'),
    path('brand-guidelines/', brand_guidelines, name='brand_guidelines'),
    path('events/', views.events, name='events'),
    path('search-trends/', search_trends, name='search_trends'),
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    path('license-agreement/', views.license_agreement, name='license_agreement'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('copyright-information/', views.copyright_information, name='copyright_information'),
    path('cookies-settings/', views.cookies_settings, name='cookies_settings'),
    path('cookies-policy/', views.cookies_policy, name='cookies_policy'),

    #Return, Exchange and Cancel
    path('order/<int:order_id>/request/<str:action>/', views.request_order_action, name='request_action'),
    path('order/<int:order_id>/return/', views.request_return, name='request_return'),
    path('order/<int:order_id>/exchange/', views.request_exchange, name='request_exchange'),
    
    path('return-success/', return_success, name='return_success'),
    path('exchange/<int:order_id>/', views.exchange_product, name='exchange_product'),
    path('confirm-exchange/', confirm_exchange, name='confirm_exchange'),
    path('cancel-success/', cancel_success, name='cancel_success'),
    
    #Review Section
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', submit_review, name='submit_review'),
    
    path('return-policy/', return_policy, name='return_policy'),
    path('shipping-policy/', shipping_policy, name='shipping_policy'),
    
    # Download Invoice URL
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),

    # Payment URLs
    path('card-payment/<int:order_id>/', views.card_payment, name='card_payment'),
    path('process-payment/', views.process_payment, name='process_payment'),

    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    path('check-username/', views.check_username, name='check_username'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)