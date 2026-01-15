from django.db import models
from customer.models import Customer
from deposite.models import Deposite
from expense.models import Expense

from django.utils import timezone

# Create your models here.

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)

    credit_amt = models.IntegerField(default=0)
    debit_amt = models.IntegerField(default=0)

    description = models.CharField(default="")
    deposite_type = models.CharField(default="other")
    expense_type = models.CharField(default="other")

    customer_id = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="f_customer_id",
        default=0
    )
    
    # deposite_id = models.ForeignKey(
    #     Deposite,
    #     on_delete=models.CASCADE,
    #     related_name="f_deposite_id",
    #     default=0
    # )
    # expense_id = models.ForeignKey(
    #     Expense,
    #     on_delete=models.CASCADE,
    #     related_name="f_expense_id",
    #     default=0
    # )

