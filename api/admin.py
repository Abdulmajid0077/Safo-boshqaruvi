from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.forms.widgets import SplitDateTimeWidget
from decimal import Decimal
from django import forms
from .models import Branch, Worker, Product, Supplier, Customer, Sale, SaleItem, AddProduct, History, AddProductItem, Expense, Investor, DailyReport

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'location')
    search_fields = ('name', 'location')
    ordering = ('-id',)

@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'age', 'phone_number', 'formatted_invest', 'created_at')
    search_fields = ('name',)
    autocomplete_fields = ('branch', )
    list_filter = ('branch', )
    ordering = ('-created_at',)

    @admin.display(description="Sarmoya ")
    def formatted_invest(self, obj):
        amount = obj.invest or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())

        if obj.currency == 'UZS':
            return f"{amount_str} so‘m"
        return f"${amount_str}"
    

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'position')
    autocomplete_fields = ('branch', )
    search_fields = ('name','position')
    list_filter = ('branch',)
    ordering = ('-id',)



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'formatted_cost_price', 'formatted_sale_price', 'quantity_format')
    search_fields = ('name', 'barcode')
    autocomplete_fields = ('branch', )
    list_filter = ('branch',)
    ordering = ('-id',)

    @admin.display(description="Mavjud miqdor")
    def quantity_format(self, obj):
        amount = obj.quantity or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())

        
        return f"{amount_str} dona"
        


    @admin.display(description="Sotib olish narxi")
    def formatted_cost_price(self, obj):
        amount = obj.cost_price or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())
        
        return f"{amount_str} so‘m"
    
    @admin.display(description="Sotish narxi")
    def formatted_sale_price(self, obj):
        amount = obj.sale_price or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())
        
        return f"{amount_str} so‘m"
    

@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('worker', 'product', 'change_type', 'formatted_quantity_changed', 'changed_at', )
    search_fields = ('product__name', 'worker__name')
    list_filter = ('worker', 'branch', 'change_type', 'changed_at')
    actions = ['delete_selected']
    ordering = ('-changed_at',)
    actions_on_top = True
    actions_on_bottom = True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    @admin.display(description="O'zgargan miqdor")
    def formatted_quantity_changed(self, obj):
        qty = obj.quantity_changed or Decimal('0')
        if qty == qty.to_integral_value():
            return f"{int(qty)}"
        return str(qty)


    # def has_delete_permission(self, request, obj=None):
    #     return False
    
class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = '__all__'
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'custom-input',
                'placeholder': 'Miqdor',
            }),
        }


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    form = SaleItemForm
    extra = 1
    autocomplete_fields = ('product',)
    fields = ('product', 'quantity', 'total_price')
    readonly_fields = ('total_price',)



@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('worker', 'amount_with_currency', 'formatted_discount', 'formatted_total_price', 'sold_at',)
    autocomplete_fields = ('customer', 'worker', 'branch')
    search_fields = ('worker', )
    inlines = [SaleItemInline]

    fieldsets = (
        ('🧾 Savdo maʼlumotlari', {
            'fields': ('branch', 'worker', 'customer'),
        }),
        ('💰 Hisob-kitob', {
            'fields': ('total_price', 'amount', 'discount'),
        }),
    )

    readonly_fields = ('total_price', 'discount', )

    @admin.display(description="To'langan summa")
    def amount_with_currency(self, obj):
        amount = obj.amount or Decimal('0')

        # Decimal bo‘lib qoladi, faqat ko‘rinishda .00 olib tashlanadi
        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())

        if obj.currency == 'UZS':
            return f"{amount_str} so‘m"
        return f"${amount_str}"


    @admin.display(description="To'plam")
    def formatted_total_price(self, obj):
        amount = obj.total_price or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())

        if obj.currency == 'UZS':
            return f"{amount_str} so‘m"
        return f"${amount_str}"
    
    @admin.display(description="Chegirma")
    def formatted_discount(self, obj):
        amount = obj.discount or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())

        if obj.currency == 'UZS':
            return f"{amount_str} so‘m"
        return f"${amount_str}"



class AddProductItemInline(admin.TabularInline):
    model = AddProductItem
    extra = 1
    autocomplete_fields = ('product', )
    readonly_fields = ('total_price', 'added_quantity',)


@admin.register(AddProduct)
class AddProductAdmin(admin.ModelAdmin):
    inlines = [AddProductItemInline]
    list_display = ('id', 'worker', 'added_at')
    autocomplete_fields = ('branch', 'worker', 'supplier')
    ordering = ('-added_at',)
    

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'formatted_debt', 'description')
    search_fields = ('name', 'phone_number')
    autocomplete_fields = ('branch', )
    ordering = ('-id',)

    @admin.display(description="Summa")
    def formatted_debt(self, obj):
        amount = obj.debt or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())
        
        return f"{amount_str} so‘m"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'debt', 'description')
    search_fields = ('name', 'phone_number')
    autocomplete_fields = ('branch', )
    ordering = ('-id', )
    fieldsets = (
        ("Asosiy ma’lumotlar", {
            "fields": ("name", "phone_number"),
        }),
        ("Moliyaviy", {
            "fields": ("debt",),
        }),
        ("Izoh", {
            "fields": ("description",),
        }),
    )

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('worker', 'category', 'formatted_amount', 'description', 'incurred_at')
    search_fields = ('worker', )
    list_filter = ('branch',)
    autocomplete_fields = ('branch', 'worker', )
    ordering = ('-id',)

    @admin.display(description="Summa")
    def formatted_amount(self, obj):
        amount = obj.amount or Decimal('0')

        if amount == amount.to_integral_value():
            amount_str = intcomma(amount.quantize(Decimal('1')))
        else:
            amount_str = intcomma(amount.normalize())
        
        return f"{amount_str} so‘m"
    

@admin.register(DailyReport)
class DailyReportAdmin(ModelAdmin):
    list_display = ["start_datetime", "end_datetime", "created_at"]
    search_fields = ["branch", ]
    list_filter = ["branch", ]
    autocomplete_fields = ["branch", ]
    ordering = ["-created_at",]

    readonly_fields = ["total_sales"]

    fieldsets = (
        ("Filial", {
            "fields": ("branch", "start_datetime", "end_datetime")
        }),
        ("Natijalar", {
            "fields": ("total_sales",),
        }),
    )


