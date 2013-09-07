from django.db import models
from django.utils import timezone
from userena.utils import get_user_model
from accounts.models import Profile

class Author(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

TYPE_CHOICES = (
    ('BO', 'BO'),
    ('CD', 'CD'),
    ('DVD', 'DVD'),
)

PDF_CHOICES = (
    ('PD', 'PD'),
    ('BO', 'BO'),
    ('PA', 'PA'),
)

LAN_CHOICES = (
    ('English', 'English'),
    ('Chinese', 'Chinese'),
    ('Other', 'Other'),
)

CONDITION_CHOICES = (
    ('NE', 'NE'),
    ('LN', 'LN'),
    ('GO for New', 'GO for New'),
    ('Like New', 'Like New'),
    ('Good', 'Good'),
)

class Material(models.Model):
    title = models.CharField(max_length=255)
    author = models.ManyToManyField(Author, null=True, blank=True)
    publisher = models.ForeignKey(Publisher, null=True, blank=True)
    giver = models.ForeignKey(get_user_model())
    isbn = models.CharField(max_length=100, blank=True)
    publisher_book_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    pages = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    create_date = models.DateTimeField(default=timezone.now)
    language = models.CharField(max_length=10, choices=LAN_CHOICES, blank=True)
    has_pic = models.BooleanField(default=False)
    pdf = models.CharField(max_length=10, choices=PDF_CHOICES)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='Good')
    quantity = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return self.title

    def get_author_names(self):
        return ', '.join(a.name for a in self.author.all())
    
    def get_quantity_nums(self):
        return range(1, self.quantity + 1)

STATUS_CHOICES = (
    ('ACT', 'ACT'),
    ('INA', 'INA'),
)


class GiverMaterial(models.Model):
    giver = models.ForeignKey(get_user_model())
    material = models.ForeignKey(Material)
    count = models.PositiveIntegerField(default=0)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    create_date = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)


class Order(models.Model):
    reader = models.ForeignKey(get_user_model())
    material = models.ForeignKey(Material)
    quantity = models.PositiveIntegerField(default=1)
    
    #~ reader = models.ForeignKey(get_user_model(), related_name='reader_orders')
    #~ giver = models.ForeignKey(get_user_model(), related_name='giver_orders')
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    order_date = models.DateTimeField(default=timezone.now)
    ship_date = models.DateTimeField(null=True, blank=True)
    pay_date = models.DateTimeField(null=True, blank=True)
    payment_detail = models.TextField(blank=True)


#~ class OrderDetail(models.Model):
    #~ order = models.ForeignKey(Order)
    #~ giver_material = models.ForeignKey(GiverMaterial)
    #~ material = models.ForeignKey(Material)
    #~ count = models.PositiveIntegerField(default=0)

