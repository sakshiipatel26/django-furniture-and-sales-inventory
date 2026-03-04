from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Cart, CartItem, Order, OrderItem, UserProfile
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm
from django.db.models import Q
import razorpay
import json
import time
from django.utils.timezone import now
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Order
from django.contrib.auth.models import User
import uuid
from django import forms
from .models import Review
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from django.shortcuts import get_object_or_404
from .models import Advertisement
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import os
import logging
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from .models import Return, Exchange
from .forms import ReturnForm, ExchangeForm
from django.core.mail import send_mail
from .models import Order, Exchange, Product, Notification
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
from django.core.mail import send_mail
import random
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
import random
from django.http import JsonResponse
from django.core.mail import send_mail
import random
from django.http import JsonResponse
from django.core.mail import send_mail
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.http import JsonResponse
import random
import random
from django.core.mail import send_mail
from django.http import JsonResponse
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

def send_otp(request):
    email = request.GET.get('email')
    if email:
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['otp_email'] = email
        request.session.modified = True  # important!

        # Send email
        send_mail(
            'Your OTP Code',
            f'Your OTP is {otp}',
            'youremail@gmail.com',  # use settings.DEFAULT_FROM_EMAIL ideally
            [email],
            fail_silently=False
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        otp = request.POST['otp']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        session_otp = request.session.get('otp')
        session_email = request.session.get('otp_email')

        if email != session_email or otp != session_otp:
            return render(request, 'store/auth/register.html', {'error': 'Invalid OTP or email mismatch'})

        if password1 != password2:
            return render(request, 'store/auth/register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'store/auth/register.html', {'error': 'Username already exists'})

        if User.objects.filter(email=email).exists():
            return render(request, 'store/auth/register.html', {'error': 'Email already in use'})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        return redirect('home')  # or any success page

    return render(request, 'store/auth/register.html')

def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    now = timezone.now()
    advertisements = Advertisement.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
    return render(request, 'store/home.html', {
        'categories': categories,
        'advertisements': advertisements
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()  # Fetch all reviews related to the product
    return render(request, 'store/product_detail.html', {'product': product, 'reviews': reviews})

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")
        Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
        return redirect("product_detail", product_id=product.id)

    return render(request, "submit_review.html", {"product": product})

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category_detail.html', {'category': category, 'products': products})

def categories(request):
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'categories': categories})

def about(request):
    return render(request, 'store/about.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Check if user exists and is active
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Prevent admin users from logging into customer site
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Administrators must use the admin login page')
                return render(request, 'store/auth/login.html', 
                    {'error': 'This login is for customers only. Administrators please use the admin login page.'})
            
            # Check if user is a customer
            try:
                profile = user.userprofile
                if profile.user_type == 'customer':
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid account type')
                    return render(request, 'store/auth/login.html', 
                        {'error': 'This account is not authorized for customer login'})
            except:
                messages.error(request, 'Invalid account type')
                return render(request, 'store/auth/login.html', 
                    {'error': 'Invalid account type'})
        else:
            return render(request, 'store/auth/login.html', 
                {'error': 'Invalid username or password'})
            
    return render(request, 'store/auth/login.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set user type as customer by default
            profile = user.userprofile
            profile.user_type = 'customer'
            profile.save()

            # Add user to customer group
            customer_group, created = Group.objects.get_or_create(name='Customers')
            user.groups.add(customer_group)

            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            return render(request, 'store/auth/register.html', {'error': form.errors})
    return render(request, 'store/auth/register.html')

@login_required
def profile_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        # Ensure username and email are unique before updating
        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, "Email already in use.")
        else:
            request.user.username = username
            request.user.email = email
            request.user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')  # Redirect to profile page after update

    return render(request, 'store/profile.html')

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

     # Get current price (either discounted or regular)
    current_price = product.discounted_price if product.has_active_discount() else product.price
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        defaults={
            'price': current_price,
            'quantity': 1
        }
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.price = current_price  # Update price in case it changed
        cart_item.save()
    
    messages.success(request, f"{product.name} added to cart!")
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        item.quantity = quantity
        # Check stock availability
        if quantity > item.product.stock:
            messages.warning(request, f"Sorry, only {item.product.stock} unit(s) available!")
            quantity = item.product.stock
            
         # Update price to current price
        current_price = item.product.discounted_price if item.product.has_active_discount() else item.product.price
        item.price = current_price
        item.save()
    else:
        item.delete()
        
    return redirect('cart')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method', 'cod')

        if not shipping_address:
            messages.error(request, "Shipping address is required.")
            return redirect('checkout')

        try:
            # Create the order
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.get_total(),
                shipping_address=shipping_address,
                status='pending' if payment_method == 'cod' else 'paid'
            )

            # Create order items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Clear the cart
            cart.items.all().delete()

            if payment_method == 'card':
                return redirect('card_payment', order_id=order.id)
            else:  # COD
                messages.success(request, "Order placed successfully!")
                return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, "An error occurred while processing your order.")
            return redirect('checkout')

    return render(request, 'store/checkout.html', {'cart': cart})

@login_required
def card_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/card_payment.html', {
        'order_id': order.id,
        'amount': order.total_amount
    })

@login_required
def process_payment(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Save card details
        order.payment_method = 'card'
        order.card_holder = request.POST.get('card_holder')
        order.card_number = request.POST.get('card_number').replace(' ', '')
        order.card_expiry = request.POST.get('expiry_date')
        order.status = 'confirmed'
        order.save()
        
        messages.success(request, "Payment processed successfully!")
        return redirect('order_confirmation', order_id=order.id)
    return redirect('checkout')

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})

def search(request):
    query = request.GET.get('q', '')
    if query:
        # Search in both products and categories
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        categories = Category.objects.filter(
            Q(name__icontains=query) 

        )
    else:
        products = []
        categories = []

    context = {
        'query': query,
        'products': products,
        'categories': categories
    }
    return render(request, 'store/search_results.html', context)

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        # Here, you can save the message or send an email
        return render(request, "store/contact.html", {"message_sent": True})

    return render(request, "store/contact.html")
       
@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/track_order.html', {'order': order})

@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('created_at')
    return render(request, 'store/orders_list.html', {'orders': orders})       

def pricing(request):
    return render(request, "store/pricing.html")

def jobs(request):
    return render(request, 'store/jobs.html')

def brand_guidelines(request):
    return render(request, 'store/brand_guidelines.html')

def events(request):
    return render(request, 'store/events.html')

def search_trends(request):
    return render(request, 'store/search_trends.html')

def terms_of_use(request):
    return render(request, 'store/terms_of_use.html')

def license_agreement(request):
    return render(request, 'store/license_agreement.html')

def privacy_policy(request):
    return render(request, 'store/privacy_policy.html')

def copyright_information(request):
    return render(request, 'store/copyright_information.html')

def cookies_settings(request):
    return render(request, 'store/cookies_settings.html')

def cookies_policy(request):
    return render(request, 'store/cookies_policy.html')

def return_success(request):
    return render(request, 'store/return_success.html')

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    return render(request, 'store/category_products.html', {'category': category, 'products': products})

def cancel_success(request):
    return render(request, 'store/cancel_success.html')

def request_order_action(request, order_id, action):
    order = get_object_or_404(Order, id=order_id)
    
    if order.status != "delivered":
        messages.error(request, "You can only request return, exchange, or cancellation after delivery.")
        return redirect("orders_list")

    if action == "return":
        order.return_status = "return_requested"
        messages.success(request, "Return request submitted successfully.")
    elif action == "exchange":
        order.return_status = "exchange_requested"
        messages.success(request, "Exchange request submitted successfully.")
    elif action == "cancel":
        order.return_status = "cancellation_requested"
        messages.success(request, "Cancellation request submitted successfully.")

    order.save()
    return redirect("orders_list")

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        if order.status in ['pending', 'confirmed']:
            order.status = 'cancelled'
            order.save()
            messages.success(request, 'Order cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
    
    return redirect('track_order', order_id=order.id)

def return_policy(request):
    return render(request, 'store/return_policy.html')

def shipping_policy(request):
    return render(request, 'store/shipping_policy.html')


#Invoice 
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # Page dimensions

    # Colors and Fonts
    primary_color = colors.HexColor("#1C5274")  # Brownish-gold from reference
    header_color = colors.black
    text_color = colors.black

    # Load Logo
    logger = logging.getLogger(__name__)
    logo_path = os.path.join(settings.BASE_DIR, "store", "static", "Site_logo.png")
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            # Adjust size and position of logo
            p.drawImage(logo, 250, height - 120, width=150, height=80, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            logger.error(f"Error loading logo: {e}")
    else:
        logger.error("Logo file not found at: " + logo_path)

    # Add some spacing after logo
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 150, "STYLENEST FURNITURE")

    # Invoice Details
    p.setFont("Helvetica", 10)
    info_x, info_y = 450, height - 210
    p.drawString(info_x, info_y, f"Date: {order.created_at.strftime('%d-%b-%Y')}")
    p.drawString(info_x, info_y - 15, f"Invoice No: {order.id:05d}")

    # Address Sections
    section_y = height - 210
    p.setFillColor(primary_color)
    p.setFont("Helvetica-Bold", 12)
    
    p.drawString(40, section_y, "FROM")
    p.drawString(250, section_y, "BILL TO")

    p.setFont("Helvetica", 10)
    p.setFillColor(text_color)
    
    # FROM (Company Details)
    from_y = section_y - 15
    p.drawString(40, from_y, "StyleNest Furnitures")
    p.drawString(40, from_y - 15, "Dr. H.M. Patel Complex, Anand,")
    p.drawString(40, from_y - 30, "Gujarat 388120")
    p.drawString(40, from_y - 45, "Phone: (555) 123-4567")
    p.drawString(40, from_y - 60, "Email: stylenestt25@gmail.com")

    # BILL TO (Customer)
    p.drawString(250, from_y, order.user.get_full_name() or order.user.username)
    clean_address = order.shipping_address.replace("\n", " ").replace("\t", " ")
    p.drawString(250, from_y - 15, clean_address)
    p.drawString(250, from_y - 30, f"Email: {order.user.email}")

   

    # Table Header
    table_y = section_y - 110
    p.setFillColor(primary_color)
    p.rect(40, table_y, 520, 20, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(45, table_y + 5, "DESCRIPTION")
    p.drawString(320, table_y + 5, "QUANTITY")
    p.drawString(400, table_y + 5, "UNIT PRICE")
    p.drawString(500, table_y + 5, "TOTAL")
    p.setFillColor(text_color)

    # Define rupee symbol with unicode
    rupee = u'\u20B9'  # Unicode for Indian Rupee symbol

    # Table Rows
    row_y = table_y - 20
    p.setFont("Helvetica", 10)
    line_height = 20
    
    # Updated way to access order items with rupee symbol
    for item in order.items.all():
        p.drawString(45, row_y, item.product.name[:40])
        p.drawString(320, row_y, str(item.quantity))
        p.drawString(400, row_y, f"Rs.{item.price:.2f}")  # Changed ₹ to Rs.
        total = item.price * item.quantity
        p.drawString(500, row_y, f"Rs.{total:.2f}")  # Changed ₹ to Rs.
        row_y -= line_height

        # Line Separator
        p.line(40, row_y + 10, 560, row_y + 10)
        row_y -= 10

    # Total Calculation with rupee symbol
    totals_y = row_y - 30
    p.setFont("Helvetica-Bold", 10)

    subtotal = sum(item.price * item.quantity for item in order.items.all())
    p.drawString(400, totals_y, "SUBTOTAL:")
    p.drawString(500, totals_y, f"Rs.{subtotal:.2f}")  # Changed ₹ to Rs.
    totals_y -= 20

    tax_amount = subtotal * Decimal("0.10")
    p.drawString(400, totals_y, "TAX (10%):")
    p.drawString(500, totals_y, f"Rs.{tax_amount:.2f}")  # Changed ₹ to Rs.
    totals_y -= 20

    shipping_fee = Decimal("50.00")
    p.drawString(400, totals_y, "SHIPPING:")
    p.drawString(500, totals_y, f"Rs.{shipping_fee:.2f}")  # Changed ₹ to Rs.
    totals_y -= 20

    total_amount = order.total_amount + tax_amount + shipping_fee
    p.drawString(400, totals_y, "TOTAL:")
    p.drawString(500, totals_y, f"Rs.{total_amount:.2f}")  # Changed ₹ to Rs.

    p.line(400, totals_y - 5, 560, totals_y - 5)

    # Notes Section
    notes_y = totals_y - 50
    p.setFont("Helvetica", 9)
    p.drawString(40, notes_y, "NOTES:")
    p.line(90, notes_y, 560, notes_y)
    p.line(40, notes_y - 10, 560, notes_y - 10)
    p.line(40, notes_y - 20, 560, notes_y - 20)

    # Payment Instructions
    p.setFont("Helvetica-Bold", 9)
    p.drawString(40, notes_y - 50, "Payment Instructions:")
    p.setFont("Helvetica", 8)
    p.drawString(40, notes_y - 65, "Bank Name: Bank of Baroda")
    p.drawString(40, notes_y - 80, "Account Name: StyleNest Furnitures")
    p.drawString(40, notes_y - 95, "Account Number: 1234-5678-9012-3456")
    p.drawString(40, notes_y - 110, "IFSC Code: BARB0ANANDX")

    # Footer
    footer_y = 50
    p.setFont("Helvetica", 8)
    p.drawCentredString(width / 2, footer_y, "Thank you for your business!")
    p.drawCentredString(width / 2, footer_y - 15, "Terms: Payment due within 7 days of invoice date")
    p.drawCentredString(width / 2, footer_y - 30, "StyleNest Furnitures")

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response
import textwrap

def format_text(text, max_width=50):
    """Preserves user formatting while ensuring no black squares."""
    clean_text = text.encode("utf-8", "ignore").decode("utf-8")  # Remove any hidden invalid characters
    return textwrap.fill(clean_text, width=max_width)  # Wrap long lines properly

@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.order = order
            return_request.user = request.user
            return_request.save()
            messages.success(request, 'Return request submitted successfully.')
            return redirect('track_order', order_id=order_id)
    else:
        form = ReturnForm()
    
    return render(request, 'store/return_form.html', {
        'form': form,
        'order': order
    })

@login_required
def request_exchange(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        form = ExchangeForm(request.POST)
        if form.is_valid():
            exchange_request = form.save(commit=False)
            exchange_request.order = order
            exchange_request.user = request.user
            exchange_request.status = "pending"  # Match the `Exchange` model status choices
            exchange_request.save()

            messages.success(request, "Exchange request submitted successfully.")
            return redirect("track_order", order_id=order.id)
    else:
        form = ExchangeForm()

    return render(request, "store/exchange_form.html", {"form": form, "order": order})


@login_required
def exchange_product(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Fetch products excluding the one in the original order
    products = Product.objects.exclude(id__in=[item.product.id for item in order.items.all()])

    if request.method == "POST":
        new_product_id = request.POST.get("new_product")
        new_product = get_object_or_404(Product, id=new_product_id)

        # Create new order for exchanged product
        new_order = Order.objects.create(
            user=request.user,
            total_amount=new_product.price,  # Adjust price
            status="Processing",  # New order starts processing
            created_at=now(),
        )

        # Add exchanged product to new order
        OrderItem.objects.create(
            order=new_order,
            product=new_product,
            quantity=1,
            price=new_product.price
        )

        # Link new order to exchange request
        exchange_request = Exchange.objects.filter(order=order, status="pending").first()
        if exchange_request:
            exchange_request.new_order = new_order
            exchange_request.status = "approved"
            exchange_request.save()

        # Notify user
        Notification.objects.create(
            user=request.user,
            message=f"Your exchange has been approved! New Order #{new_order.id} is now processing."
        )

        messages.success(request, "Exchange processed successfully. You can track your new order.")
        return redirect("track_order", order_id=new_order.id)

    return render(request, "store/exchange_form.html", {"order": order, "products": products})

def confirm_exchange(request):
    return render(request, "store/confirm_exchange.html")

from django.http import JsonResponse
from django.contrib.auth.models import User

def check_username(request):
    username = request.GET.get('username', '')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': exists})
