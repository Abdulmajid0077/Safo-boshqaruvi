from django.db import models, transaction
from decimal import Decimal
from django.forms import ValidationError
from .branchstock import Branch, Product, Worker, History, AddProductItem
from django.db.models import Sum, F

class Customer(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='customers', verbose_name="Filial")
    name = models.CharField(max_length=100, verbose_name="Ismi")
    phone_number = models.CharField(max_length=15, verbose_name="Telefon raqami")
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Qarz miqdori")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kiritilgan vaqti")

    def __str__(self):
        return f"{self.name} - {self.debt} so'm"


class Sale(models.Model):
    CURRENCY_CHOICES = (
        ('UZS', "So'm"),
        ('USD', "Dollar"),
    )

    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE,
        related_name='sales', null=True, verbose_name="Filial"
    )
    worker = models.ForeignKey(
        Worker, on_delete=models.CASCADE,
        related_name='sales', verbose_name="Hodim"
    )

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="To'plam")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="To'langan summa")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES,default='UZS', verbose_name="Valyuta")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Chegirma")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales', null=True, blank=True, verbose_name="Qarzdor")
    sold_at = models.DateTimeField(auto_now_add=True, verbose_name="Sotish vaqti")

    def __str__(self):
        return f"Sale {self.id}"

    # 🔹 Itemlar o‘zgarganda chaqiriladi
    def recalc_total(self):
        total = self.items.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')

        self.total_price = total
        self._recalc_discount()
        self.save(update_fields=['total_price', 'discount'])

    # 🔹 Chegirmani bitta joyda hisoblash
    def _recalc_discount(self):
        amount = Decimal(self.amount or 0)
        total = Decimal(self.total_price or 0)

        if amount < total:
            self.discount = total - amount
        else:
            self.discount = Decimal('0')

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        old_amount = Decimal('0')
        if not is_new:
            old_amount = Decimal(
                str(Sale.objects.get(pk=self.pk).amount or 0)
            )

        self._recalc_discount()

        if self.customer:
            customer_obj, _ = Customer.objects.get_or_create(
                name=self.customer.name,
                phone_number=self.customer.phone_number,
                defaults={
                    'branch': self.branch,
                    'debt': Decimal('0')
                }
            )
            self.customer = customer_obj

        super().save(*args, **kwargs)

        if self.customer:
            new_amount = Decimal(str(self.amount or 0))
            debt_diff = new_amount - old_amount

            if debt_diff != 0:
                self.customer.debt = (
                    self.customer.debt or Decimal('0')
                ) + debt_diff
                self.customer.save(update_fields=['debt'])

    @transaction.atomic
    def delete(self, *args, **kwargs):
            if self.customer:
                self.customer.debt -= self.amount
                if self.customer.debt < 0:
                    self.customer.debt = 0
                self.customer.save()
            super().delete(*args, **kwargs)
    
            
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Miqdor")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sold_at = models.DateTimeField(auto_now_add=True, verbose_name="Sotish vaqti")

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    def clean(self):
        if self.pk is None:
            if self.product.quantity < Decimal(self.quantity):
                raise ValidationError("Omborda yetarli mahsulot yo‘q")


    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_quantity = Decimal('0')

        if not is_new:
            old_quantity = SaleItem.objects.get(pk=self.pk).quantity

        self.total_price = Decimal(self.product.sale_price) * Decimal(self.quantity)

        delta = self.quantity if is_new else (self.quantity - old_quantity)

        if delta > 0 and self.product.quantity < delta:
            raise ValidationError("Omborda yetarli mahsulot yo‘q")

        super().save(*args, **kwargs)

        self.sale.recalc_total()

        if delta == 0:
            return

        self.product.quantity = F('quantity') - delta
        self.product.save(update_fields=['quantity'])

        History.objects.create(
            branch=self.sale.branch,
            worker=self.sale.worker,
            product=self.product,
            change_type="Sotildi",
            quantity_changed=delta
        )
        

from django.db import models
from django.db.models import Sum

class DailyReport(models.Model):
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, related_name='daily_reports', verbose_name="Filial")
    start_datetime = models.DateTimeField(verbose_name="Qachondan ")
    end_datetime = models.DateTimeField(verbose_name="Qachongahca ")
    
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jami kassa")
    total_discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jami chegirmalar")
    total_purchase = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jami sotib olishlar")
    total_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jami qarzlar")   
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    
    
    def __str__(self):
        return f"{self.branch.name}: {self.start_datetime} - {self.end_datetime}"
    
    def save(self, *args, **kwargs):
        if self.branch and self.start_datetime and self.end_datetime:
            # Jami savdo va chegirmalar
            sales_qs = Sale.objects.filter(
                branch=self.branch,
                sold_at__gte=self.start_datetime,
                sold_at__lte=self.end_datetime
            )
            self.total_sales = sales_qs.aggregate(total=Sum('total_price'))['total'] or 0
            self.total_discounts = sales_qs.aggregate(total=Sum('discount'))['total'] or 0

            # Jami sotib olishlar (AddProductItem summasidan)
            purchase_qs = AddProductItem.objects.filter(
                branch=self.branch,
                added_at__gte=self.start_datetime,
                added_at__lte=self.end_datetime
            )
            self.total_purchase = purchase_qs.aggregate(total=Sum('total_price'))['total'] or 0

            # Jami qarzlar (branch bo‘yicha)
            debt_qs = Customer.objects.filter(branch=self.branch)
            self.total_debt = debt_qs.aggregate(total=Sum('debt'))['total'] or 0

        super().save(*args, **kwargs)
