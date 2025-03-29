from math import prod
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from .token import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.http import JsonResponse

from .models import User, Item, OrderedItem


def index(request):
    title_filter = request.GET.get("title", "")  # Get the title filter, default to empty string
    type_filter = request.GET.get("type", None)  # Get the type filter

    # Filter items based on type and title
    items = Item.objects.all()
    if type_filter:
        items = items.filter(category=type_filter)

    if title_filter:
        items = items.filter(title__icontains=title_filter)  # Filter items that contain the title

    paginator = Paginator(items, 8)  # Paginate the filtered items
    page_range = paginator.page_range

    if request.GET.get("page") != None:
        page = int(request.GET.get("page"))
        if page > paginator.num_pages:
            return HttpResponse("You have selected a nonexistent page.")
        paginator = paginator.page(page)
    else:
        page = 1
        paginator = paginator.page(1)

    return render(request, 'home-page.html', {
        'products': paginator,
        'type': type_filter,
        'page_range': page_range,
        'page': page,
        'title_filter': title_filter  # Pass the title filter to the template for the input field
    })


def product(request, name):
    product = Item.objects.get(title=name)
    return render(request, 'product-page.html', {
        'product': product,
        'message': "",
        'success': ""
    })


def add_item(request, id):
    if request.method == "POST":
        product = Item.objects.get(pk=id)
        quantity = int(request.POST["quantity"])
        size = request.POST.get("size", False)

        if quantity <= 0 or quantity > 9 or size == False:
            return render(request, 'product-page.html', {
                'product': product,
                'message': "Quantity invalid or size not slected!",
                'success': ""
            })

        ordered_product = OrderedItem.objects.filter(
            user=request.user, item=product, size=size).first()
        if ordered_product:
            ordered_product.quantity += quantity
            if ordered_product.quantity > 9:
                return render(request, 'product-page.html', {
                    'product': product,
                    'message': "Can't have more than 9 products of one type in your cart",
                    'success': ""
                })
            ordered_product.save()
        else:
            ordered_product = OrderedItem.objects.create(
                user=request.user, item=product, size=size, quantity=quantity)
            ordered_product.save()

        return render(request, 'product-page.html', {
            'product': product,
            'message': "",
            'success': "Items added to cart"
        })


@login_required
def checkout(request):
    ordered_items = request.user.items.all()
    return render(request, 'checkout-page.html', {
        'ordered_items': ordered_items
    })


@login_required
def order(request):
    if request.method == "POST":
        if not request.user.items.exists():
            return redirect('checkout')

        country = request.POST["country"]
        county = request.POST["county"]
        zip = request.POST["zip"]
        address = request.POST["address"]
        city = request.POST["city"]

        ordered = request.user.items.all()
        total = 0
        for item in ordered:
            total += item.quantity * item.item.price

        mail_subject = 'WeSellClothes order confirmation'

        message = render_to_string('order_confirmation_email.html', {
            'ordered': ordered,
            'country': country,
            'zip': zip,
            'county': county,
            'address': address,
            'user': request.user,
            'total': total,
            'city': city
        })

        email = EmailMessage(
            subject=mail_subject,
            body=message,
            from_email='your_email@example.com',  # Replace with your email
            to=[request.user.email]
        )
        email.content_subtype = "html"

        email.send()

        for item in ordered:
            item.delete()

        return render(request, "order-page.html", {
            "success": "Your order has been successfully sent. Check your email for confirmation."
        })
    else:
        if not request.user.items.exists():
            return redirect('checkout')

        ordered = request.user.items.all()
        total = 0
        for item in ordered:
            total += item.quantity * item.item.price
        return render(request, 'order-page.html', {
            'total': total - 10,
            'success': ""
        })


@login_required
@csrf_exempt
def decrease(request, id):
    ordered_item = OrderedItem.objects.get(pk=id)

    if request.method == "POST" and request.user == ordered_item.user:
        ordered_item.quantity -= 1

        if ordered_item.quantity < 1:
            return JsonResponse({"error": "Quantity would become less than 1. Try delete button."}, status=401)

        ordered_item.save()

        return JsonResponse(
            {"quantity": ordered_item.quantity, "price": ordered_item.item.price * ordered_item.quantity}, status=200)
    else:
        return JsonResponse({"error": "POST method required!"}, status=402)


@login_required
@csrf_exempt
def increase(request, id):
    ordered_item = OrderedItem.objects.get(pk=id)

    if request.method == "POST" and request.user == ordered_item.user:
        ordered_item.quantity += 1

        if ordered_item.quantity > 9:
            return JsonResponse({"error": "You can't order more than 9 of one type of item."}, status=403)

        ordered_item.save()

        return JsonResponse(
            {"quantity": ordered_item.quantity, "price": ordered_item.item.price * ordered_item.quantity}, status=200)
    else:
        return JsonResponse({"error": "POST method required!"}, status=402)


@login_required
@csrf_exempt
def delete(request, id):
    ordered_item = OrderedItem.objects.get(pk=id)

    if request.method == "POST" and request.user == ordered_item.user:
        ordered_item.delete()

        if not request.user.items.exists():
            return JsonResponse({"success": "Success", "empty": "Empty"}, status=200)
        else:
            return JsonResponse({"success": "Success"}, status=200)
    else:
        return JsonResponse({"error": "POST method required!"}, status=402)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('index')


def register(request):
    if request.method == "POST":
        email = request.POST["email"]
        first = request.POST["first_name"]
        last = request.POST["last_name"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username=email, email=email, password=password, last_name=last,
                                            first_name=first, is_active=False)
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activation link has been sent to your email id'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email1 = EmailMessage(
                mail_subject, message, to=[email]
            )
            email1.send()
            return render(request, "register.html", {
                "success": "Check your email to activate account."
            })
        except IntegrityError:
            user = User.objects.get(email=email)
            if user.is_active == False:
                user.delete()
                user = User.objects.create_user(username=email, email=email, password=password, last_name=last,
                                                first_name=first, is_active=False)
                user.save()
                current_site = get_current_site(request)
                mail_subject = 'Activation link has been sent to your email id'
                message = render_to_string('acc_active_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                })
                email1 = EmailMessage(
                    mail_subject, message, to=[email]
                )
                email1.send()
                return render(request, "register.html", {
                    "success": "Check your email to activate account."
                })
            else:
                return render(request, "register.html", {
                    "message": "Email already taken."
                })
    else:
        return render(request, "register.html")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')