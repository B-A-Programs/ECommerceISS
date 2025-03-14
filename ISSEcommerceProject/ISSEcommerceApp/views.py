from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import Item


def index(request):
    if request.GET.get("type") != None:
        type = request.GET.get("type")
        paginator = Paginator(Item.objects.filter(category=type), 8)
    else:
        type = None
        paginator = Paginator(Item.objects.all(), 8)

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
        'type': type,
        'page_range': page_range,
        'page': page
    })


def product(request, name):
    product = Item.objects.get(title=name)
    return render(request, 'product-page.html', {
        'product': product,
        'message': "",
        'success': ""
    })