from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.items.count()
            return {'cart_count': count}
    return {'cart_count': 0}