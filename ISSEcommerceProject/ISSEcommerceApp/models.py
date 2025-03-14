from django.db import models
from django.contrib.auth.models import AbstractUser

CATEGORY_CHOICES = (
    ('S', 'Shirts'),
    ('SW', 'Sport wear'),
    ('OW', 'Out wear')
)

LABEL_CHOICES = (
    ('N', 'danger'),
    ('B', 'primary')
)


class User(AbstractUser):
    class Meta:
        ordering = ['-id']


class Item(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    price = models.FloatField()
    image_adress = models.CharField(max_length=500, null=True)

    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, null=True)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, null=True, blank=True)

    def __str__(self):
        return self.title


class OrderedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    size = models.CharField(max_length=5)

    quantity = models.IntegerField(default=1)