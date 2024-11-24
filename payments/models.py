from django.db import models


class Payment(models.Model):
    customer_email = models.EmailField(null=True, blank=True)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_type = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    payment_status = models.CharField(max_length=255, null=True, blank=True)
    receipt_url = models.URLField(max_length=2000, null=True, blank=True)
    created = models.IntegerField(null=True, blank=True)
    updated = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer_email} - {self.product_name} - ${self.amount_in_dollars}"
