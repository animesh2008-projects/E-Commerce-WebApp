from django.db.models import Sum

from .models import CartItem


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        count = (
            CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total']
            or 0
        )
    return {'cart_item_count': count}
