from django.db import models, transaction
from decimal import Decimal
from django.db.models import F

class Branch(models.Model):
    name = models.CharField(max_length=100, verbose_name="Filial nomi")
    location = models.CharField(max_length=255, verbose_name="Manzil")

    def __str__(self):
        return self.name
    
class Investor(models.Model):
    CURRENCY_CHOICES = (
        ('UZS', "So'm"),
        ('USD', "Dollar"),
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='investors', verbose_name="Filial")
    name = models.CharField(max_length=100, verbose_name="Ismi")
    surname = models.CharField(max_length=100, verbose_name="Familyasi")
    age = models.CharField(max_length=100, verbose_name="Yoshi")
    phone_number = models.CharField(max_length=15, verbose_name="Telefon raqami")
    invest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Sarmoya miqdori")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS', verbose_name="Valyuta")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kiritilgan vaqti")

class Worker(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='workers', verbose_name="Filial")
    name = models.CharField(max_length=100, verbose_name="Ismi")
    phone_number = models.CharField(max_length=15, verbose_name="Telefon raqami")
    position = models.CharField(max_length=100, verbose_name="Lavozimi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kiritilgan vaqti")

    def __str__(self):
        return self.name
    
class Supplier(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='suppliers', null=True, verbose_name="Filial")
    name = models.CharField(max_length=100, verbose_name="Ismi")
    phone_number = models.CharField(max_length=15, verbose_name="Telefon raqami")
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Qarz miqdori")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kiritilgan vaqti")

    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = (
        ('pcs', 'Dona'),
        ('kg', 'Kilogramm'),
    )

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100, verbose_name="Mahsulot nomi")
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Shtrixkod")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal('0'), verbose_name="Mavjud miqdor (dona)")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sotib olish narxi")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sotish narxi")

    base_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name="Qabul birligi")
    kg_to_pcs = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="1 kg nechta dona")

    def __str__(self):
        return self.name



class AddProduct(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='add_products', null=True, verbose_name="Filial")
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='add_products', null=True, verbose_name="Hodim")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products', null=True, blank=True, verbose_name="Yetkazib beruvchi")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqti")

    def __str__(self):
        return f"Added {self.added_at}"

    @transaction.atomic
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)


class AddProductItem(models.Model):
    add_product = models.ForeignKey(
        AddProduct, on_delete=models.CASCADE,
        related_name='add_product'
    )

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='add_items',
        verbose_name="Mahsulot"
    )

    input_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name="Kiritilgan miqdor (kg yoki dona)"
    )

    added_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        editable=False,
        verbose_name="Omborga qo‘shildi (dona)"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Sotib olish narxi"
    )

    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Jami narx"
    )

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} +{self.added_quantity}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_quantity = Decimal('0')

        if not is_new:
            old_quantity = AddProductItem.objects.get(pk=self.pk).added_quantity

        if self.product.base_unit == 'kg':
            if not self.product.kg_to_pcs:
                raise ValueError(
                    f"{self.product.name} uchun 1 kg = nechta dona belgilanmagan"
                )

            self.added_quantity = (
                Decimal(self.input_quantity) * Decimal(self.product.kg_to_pcs)
            )

            unit_cost_price = (
                Decimal(self.price) / Decimal(self.product.kg_to_pcs)
            )

        else:
            self.added_quantity = Decimal(self.input_quantity)
            unit_cost_price = Decimal(self.price)

        self.total_price = self.added_quantity * unit_cost_price

        self.product.cost_price = unit_cost_price
        self.product.save(update_fields=['cost_price'])

        super().save(*args, **kwargs)

        delta = self.added_quantity - old_quantity
        self.product.quantity = F('quantity') + delta
        self.product.save(update_fields=['quantity'])

        History.objects.create(
            branch=self.add_product.branch,
            worker=self.add_product.worker,
            product=self.product,
            change_type="Qo'shildi" if delta > 0 else "O'chirildi",
            quantity_changed=abs(delta)
        )


class History(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='histories', verbose_name="Filial")
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='histories', null=True, blank=True, verbose_name="Hodim")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='histories', verbose_name="Mahsulot")

    change_type = models.CharField(max_length=50, verbose_name="O'zgarish turi")

    quantity_changed = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name="O'zgargan miqdor"
    )

    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="O'zgarish vaqti")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("History yozuvini o‘zgartirish mumkin emas")
        super().save(*args, **kwargs)


    # def delete(self, *args, **kwargs):
    #     raise ValueError("History yozuvini o‘chirish mumkin emas")


class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('do\'kon xarajatlari', 'Do\'kon xarajatlari'),
        ('shaxsiy xarajatlar', 'Shaxsiy xarajatlar'),
        ('boshqa xarajatlar', 'Boshqa xarajatlar'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses', null=True, verbose_name="Filial")
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='expenses', verbose_name="Hodim")
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES, verbose_name="Sababi")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Summa")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")
    incurred_at = models.DateTimeField(auto_now_add=True, verbose_name="Olish vaqti")

    def __str__(self):
        return f"Harajat {self.id} - {self.amount}"