from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("product/<name>", views.product, name="product"),
    #path("checkout", views.checkout, name="checkout"),
    #path("login", views.login_view, name="login"),
    #path("logout", views.logout_view, name="logout"),
    #path("register", views.register, name="register"),
    #path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',  views.activate, name='activate'),
    #path('add_item/<id>', views.add_item, name='add_item'),
    #path('order', views.order, name='order'),
    #path('decrease/<id>', views.decrease, name='decrease'),
    #path('increase/<id>', views.increase, name='increase'),
    #path('delete/<id>', views.delete, name="delete")
]