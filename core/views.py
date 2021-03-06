from django import http
from django.db import transaction
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from userena.views import signup as userena_signup

from core.models import Material, Order
from core.forms import MaterialForm, AuthorForm, PublisherForm
from accounts.models import Profile
                  
def index(request):
    if request.method == 'POST':
        material = get_object_or_404(Material, id=request.POST.get('material_id'))
        quantity = int(request.POST.get('quantity', 0))

        if request.user.is_authenticated():
            update_orders(request.user, material, quantity)
        else:
            cart = request.session.get("cart", {})
            cart[material] = quantity + cart.get(material, 0)
            request.session["cart"] = cart

    context = {
        'materials': Material.objects.all(),
    }
    return render(request, 'index.html', context)

def update_orders(user, material, quantity):
    if material.quantity < quantity:
        quantity = material.quantity

    if quantity == 0:
        return False

    with transaction.commit_on_success():
        material.quantity -= quantity
        material.save(update_fields=['quantity'])
        try:
            order = Order.objects.get(reader=user, material=material)
        except Order.DoesNotExist:
            Order.objects.create(reader=user, material=material, quantity=quantity)
        except Order.MultipleObjectsReturned:
            orders = Order.objects.filter(reader=user, material=material)
            for o in orders[1:]:
                orders[0].quantity += o.quantity
                o.delete()
            orders[0].quantity += quantity
            orders[0].save(update_fields=['quantity'])
        else:
            order.quantity += quantity
            order.save(update_fields=['quantity'])

def user_profile(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    profile = get_object_or_404(Profile, user=user)
    context = {
        'username': username,
        'user': user,
        'profile': profile,
    }
    return render(request, 'account/user_profile.html', context)

def check_out(request):
    #if not login, need to redirect to reader login page
    if not request.user.is_authenticated():
        return redirect('/accounts/signup_reader/')

    # if already login, need to validate the order
    # loop through the car to display order.
    for material, quantity in request.session.pop('cart', {}).items():
        update_orders(request.user, material, quantity)

    orders = Order.objects.filter(reader=request.user)
    context = {
        'orders': orders,
    }
    return render(request, 'check_out.html', context)

@login_required
def confirm_check_out(request):
    """
    with transaction.commit_on_success():
        quantity = int(quantity)
        if Order.objects.filter(reader=request.user, material=material):
            order = Order.objects.filter(reader=request.user, material=material)[0]
            order.quantity += quantity
            order.save(update_fields=['quantity'])
        else:
            Order.objects.create(reader=request.user, material=material, quantity=quantity)
        material.quantity -= quantity
        material.save(update_fields=['quantity'])
    """
    pass


@login_required
def account_summary(request):
    reading_orders = Order.objects.filter(reader=request.user)
    giving_orders = Order.objects.filter(material__giver=request.user)
    materials = Material.objects.filter(giver=request.user)
    context = {
        'reading_orders_new': reading_orders.filter(ship_date=None, pay_date=None).count(),
        'reading_orders_shipped': reading_orders.exclude(ship_date=None).filter(pay_date=None).count(),
        'reading_orders_delivered': reading_orders.exclude(pay_date=None).count(),
        'giving_orders_new': giving_orders.filter(ship_date=None, pay_date=None).count(),
        'giving_orders_shipped': giving_orders.exclude(ship_date=None).filter(pay_date=None).count(),
        'giving_orders_delivered': giving_orders.exclude(pay_date=None).count(),
        'materials_active': materials.filter(status='Active').count(),
        'materials_inactive': materials.filter(status='Inactive').count(),
    }
    return render(request, 'account/summary.html', context)

@login_required
def account_reading_orders(request):
    orders = Order.objects.filter(reader=request.user)
    context = {
        'orders': orders,
    }
    return render(request, 'account/orders/reading.html', context)

@login_required
def account_giving_orders(request):
    orders = Order.objects.filter(material__giver=request.user)
    context = {
        'orders': orders,
    }
    return render(request, 'account/orders/giving.html', context)

@login_required
def ship_order(request, order_id):
    next = request.GET.get('next', '/')
    try:
        order = Order.objects.get(id=order_id, material__giver=request.user)
    except Order.DoesNotExist:
        pass
    else:
        order.ship_date = timezone.now()
        order.save(update_fields=['ship_date'])
    return redirect(next)

@login_required
def account_material(request):
    materials = Material.objects.filter(giver=request.user)
    context = {
        'materials': materials,
    }
    return render(request, 'account/material.html', context)

@login_required
def account_material_edit(request, material_id=None):
    material = None
    if material_id is not None:
        material = get_object_or_404(Material, id=material_id)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            new_material = form.save(commit=False)
            new_material.giver = request.user
            new_material.save()
            form.save_m2m()
            return redirect('account_material')
    else:
        form = MaterialForm(instance=material)
    context = {
        'form': form,
        'is_editing': material is not None,
    }
    return render(request, 'account/material_edit.html', context)

@login_required
def account_add_author(request):
    next = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(next or 'account_material')
    else:
        form = AuthorForm()
    return render(request, 'account/add_author.html', {'form': form, 'next': next})

@login_required
def account_add_publisher(request):
    next = request.REQUEST.get('next', '')
    if request.method == 'POST':
        form = PublisherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(next or 'account_material')
    else:
        form = PublisherForm()
    return render(request, 'account/add_publisher.html', {'form': form, 'next': next})

def signup(request, **kwargs):
    response = userena_signup(request, **kwargs)
    if response.status_code == 302:
        messages.success(request, 'You have been signed up.')
    return response

