from django.db import models
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Category(MPTTModel):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="category_images/", null=True, blank=True)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_subcategories(self):
        return self.children.all()


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)  # Add this field
    is_available = models.BooleanField(default=True)  # Add this field
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="products/")
    ar_model = models.FileField(upload_to="ar_models/", blank=True, null=True)

    # Add discount fields
    discount_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Discount (%)",
    )
    discount_start_date = models.DateTimeField(null=True, blank=True)
    discount_end_date = models.DateTimeField(null=True, blank=True)

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def discounted_price(self):
        if self.has_active_discount():
            discount = (self.price * Decimal(self.discount_percentage)) / Decimal(100)
            return self.price - discount
        return self.price

    def has_active_discount(self):
        from django.utils import timezone

        now = timezone.now()
        if self.discount_percentage > 0:
            if self.discount_start_date and self.discount_end_date:
                return self.discount_start_date <= now <= self.discount_end_date
            return True
        return False

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_available

    def update_stock(self, quantity, operation="decrease"):
        """
        Update product stock
        operation: 'decrease' or 'increase'
        """
        if operation == "decrease":
            if self.stock >= quantity:
                self.stock -= quantity
                if self.stock == 0:
                    self.is_available = False
            else:
                raise ValidationError("Not enough stock available")
        elif operation == "increase":
            self.stock += quantity
            if self.stock > 0:
                self.is_available = True

        self.save()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def formatted_price(self):
        return f"₹{self.price:,.2f}"

    def clean(self):
        if self.ar_model:
            valid_extensions = [".glb", ".gltf"]
            if not any(self.ar_model.name.endswith(ext) for ext in valid_extensions):
                raise ValidationError(
                    f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}"
                )


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} Stars)"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_discounted_total(self):
        """Returns the total amount with discounts applied to each item."""
        return sum(item.get_discounted_cost() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)  # Changed back to auto_now_add

    def get_cost(self):
        return self.product.price * self.quantity

    def get_discounted_cost(self):
        """Returns the cost with discount applied for this cart item."""
        return self.product.discounted_price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    RETURN_STATUS_CHOICES = [
        ("none", "No Request"),
        ("return_requested", "Return Requested"),
        ("returned", "Returned"),
        ("exchange_requested", "Exchange Requested"),
        ("exchanged", "Exchanged"),
        ("cancellation_requested", "Cancellation Requested"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    return_status = models.CharField(
        max_length=25, choices=RETURN_STATUS_CHOICES, default="none"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    card_holder = models.CharField(max_length=100, null=True, blank=True)
    card_number = models.CharField(
        max_length=16, null=True, blank=True
    )  # Will store last 4 digits only
    card_expiry = models.CharField(max_length=5, null=True, blank=True)
    payment_method = models.CharField(
        max_length=20,
        default="cod",
        choices=[("cod", "Cash on Delivery"), ("card", "Card Payment")],
    )

    def get_tracking_url(self):
        return reverse("track_order", args=[self.id])

    def can_request_return(self):
        """Returns True if the order is eligible for return/exchange/cancellation."""
        return self.status == "delivered" and self.return_status == "none"

    def save(self, *args, **kwargs):
        if self.card_number and len(self.card_number) > 4:
            # Only store last 4 digits
            self.card_number = "xxxx-xxxx-xxxx-" + self.card_number[-4:]
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            # If order status changed to cancelled, return items to stock
            if old_order.status != "cancelled" and self.status == "cancelled":
                for item in self.items.all():
                    item.product.update_stock(item.quantity, "increase")
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_cost(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new order items
            # Check if enough stock is available
            if self.product.stock < self.quantity:
                raise ValidationError(
                    f"Not enough stock available for {self.product.name}"
                )
            # Decrease stock when order item is created
            self.product.update_stock(self.quantity, "decrease")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Increase stock when order item is deleted
        self.product.update_stock(self.quantity, "increase")
        super().delete(*args, **kwargs)


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [("customer", "Customer"), ("admin", "Admin")]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="customer"
    )
    reset_token = models.CharField(max_length=100, null=True, blank=True)

class Advertisement(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="advertisements/")  # Upload folder
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_visible(self):
        """Check if the ad is currently active based on date and status."""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def __str__(self):
        return self.title

class Return(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="return_set"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Exchange(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    EXCHANGE_TRACKING_STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="exchange_set"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    new_product = models.ForeignKey("Product", on_delete=models.CASCADE)
    tracking_status = models.CharField(
        max_length=20, choices=EXCHANGE_TRACKING_STATUS, default="pending"
    )  # New Field
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:30]}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, user_type="customer")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
