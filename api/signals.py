from decimal import Decimal
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import F
from api.models import SaleItem, AddProductItem, History


@receiver(post_delete, sender=SaleItem)
def saleitem_deleted(sender, instance, **kwargs):
    instance.product.quantity = F('quantity') + Decimal(instance.quantity)
    instance.product.save(update_fields=['quantity'])

    History.objects.create(
        branch=instance.sale.branch if instance.sale else None,
        worker=instance.sale.worker if instance.sale else None,
        product=instance.product,
        change_type="Sotuv bekor qilindi",
        quantity_changed=Decimal(instance.quantity)
    )


@receiver(post_delete, sender=AddProductItem)
def addproductitem_deleted(sender, instance, **kwargs):
    instance.product.quantity = F('quantity') - Decimal(instance.added_quantity)
    instance.product.save(update_fields=['quantity'])

    History.objects.create(
        branch=instance.add_product.branch,
        worker=instance.add_product.worker,
        product=instance.product,
        change_type="O'chirildi",
        quantity_changed=Decimal(instance.added_quantity)
    )

