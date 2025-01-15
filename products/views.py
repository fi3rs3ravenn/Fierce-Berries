from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login , logout

def home(request):
    query = request.GET.get('q', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    return render(request, 'products/home.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    if cart.get(str(product_id), 0) < product.stock:
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        messages.success(request, f'{product.name} добавлен в корзину.')
    else:
        messages.warning(request, f'Извините, доступно только {product.stock} шт. {product.name}.')

    request.session['cart'] = cart
    return redirect('cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    cart_items = [{'product': product, 'quantity': cart[str(product.id)]} for product in products]
    total_price = sum(item['product'].price * item['quantity'] for item in cart_items)
    return render(request, 'products/cart.html', {'cart_items': cart_items, 'total_price': total_price})


@login_required
def create_order(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        cart = request.session.get('cart', {})
        products = Product.objects.filter(id__in=cart.keys())

        if not products:
            messages.error(request, "Корзина пуста.")
            return redirect('cart')


        for product in products:
            if cart[str(product.id)] > product.stock:
                messages.error(request, f"Недостаточно товара {product.name} на складе.")
                return redirect('cart')

        total_price = sum(product.price * cart[str(product.id)] for product in products)
        order = Order.objects.create(user=request.user, name=name, phone=phone, address=address, total_price=total_price)

        for product in products:
            OrderItem.objects.create(order=order, product=product, quantity=cart[str(product.id)])
            product.stock -= cart[str(product.id)]
            product.save()

        request.session['cart'] = {}  # Очищаем корзину после успешного заказа
        messages.success(request, "Ваш заказ успешно оформлен!")
        return redirect('home')

    return render(request, 'products/order_form.html')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        if cart[str(product_id)] > 1:
            cart[str(product_id)] -= 1  
        else:
            del cart[str(product_id)]  
        messages.success(request, "Количество товара обновлено.")
    else:
        messages.warning(request, "Товар отсутствует в корзине.")
    
    request.session['cart'] = cart 
    return redirect('cart')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'products/register.html', {'form': form})

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'products/profile.html', {'orders': orders})

def logout_view(request):
    logout(request)
    return redirect('home')