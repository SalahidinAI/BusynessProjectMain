from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(AbstractUser):
    age = models.PositiveSmallIntegerField(default=0, null=True, blank=True,
                                           validators=[MinValueValidator(10), MaxValueValidator(110)])
    phone = PhoneNumberField(null=True, blank=True, region='KG')
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name

    class Meta:
        ordering = ['-date_registered']


class Seller(models.Model):
    seller_name = models.CharField(max_length=32)

    def __str__(self):
        return self.seller_name


class Group(models.Model):
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='groups_owner')
    group_name = models.DateField(default=date.today)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.group_name} - {self.products.count()}  {self.owner.first_name}'

    def get_count_products(self):
        return self.products.count()

    def get_count_sold_sizes(self):
        return ProductSize.objects.filter(product__group=self, have=False).count()

    def get_count_all_sizes(self):
        return ProductSize.objects.filter(product__group=self).count()

    def get_group_spend(self):
        all_spend = self.products.all()
        spends = sum([i.sizes.count() * i.low_price for i in all_spend])
        if spends:
            return spends
        return 0

    def get_products_income(self):
        all_income = self.products.all()
        total = sum(
            size.high_price
            for product in all_income
            for size in product.sizes.filter(have=False)
        )
        return total

    def get_products_profit(self):
        all_products = self.products.all()
        total_profit = 0
        for product in all_products:
            sold_sizes = product.sizes.filter(have=False)
            income = sum(size.high_price for size in sold_sizes)
            expense = sold_sizes.count() * product.low_price
            total_profit += income - expense
        return total_profit

    class Meta:
        ordering = ['-created_date']


class Product(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='product_image', null=True, blank=True)
    product_name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    low_price = models.PositiveSmallIntegerField()
    article = models.CharField(max_length=50, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name

    def get_products_spend(self):
        sizes = self.sizes.all()
        if sizes.exists():
            return sizes.count() * self.low_price
        return 0

    def get_products_income(self):
        sold_sizes = self.sizes.filter(have=False)
        if sold_sizes.exists():
            return sum(size.high_price for size in sold_sizes)  # убрал if size.high_price
        return 0

    def get_products_profit(self):
        sold_sizes = self.sizes.filter(have=False)
        if sold_sizes.exists():
            return sum(size.high_price for size in sold_sizes) - sold_sizes.count() * self.low_price
        return 0

    class Meta:
        ordering = ['-created_date']


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size = models.PositiveSmallIntegerField()
    have = models.BooleanField(default=True)
    high_price = models.PositiveIntegerField(null=True, blank=True)
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True, blank=True)
    seller_name = models.CharField(max_length=32, blank=True, null=True)
    sold_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.product.product_name}  {self.size}'

    def save(self, *args, **kwargs):
        if self.seller:
            self.seller_name = self.seller.seller_name
        super().save(*args, **kwargs)

    def get_queryset(self):
        return self.filter(product__group__owner=self.request.user)

    def get_profit(self):
        if self.high_price:
            return self.high_price - self.product.low_price
        return 0

    def clean(self):
        if not self.have and not self.high_price:
            raise ValidationError({'high_price': 'Поле high_price не может быть пустым, если have=False.'})

        if self.high_price is not None and self.high_price < self.product.low_price:
            raise ValidationError({'high_price': 'Поле high_price не может быть меньше, чем low_price продукта.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class SalesHistory(models.Model):
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    sold_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_size} {self.product} {self.product_size.product.article} {self.product_size.product.low_price} {self.product_size.high_price}"

    class Meta:
        ordering = ['-sold_date']
