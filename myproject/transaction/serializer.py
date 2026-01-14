from rest_framework import serializers
from .models import Transaction
from customer.models import Customer
from deposite.models import Deposite
from expense.models import Expense

class TransactionSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(max_length=50)
    date = serializers.DateTimeField(read_only=True)
    credit_amt = serializers.IntegerField(default=0)
    debit_amt = serializers.IntegerField(default=0)

    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())

    # deposite_id = serializers.PrimaryKeyRelatedField(queryset=Deposite.objects.all())
    # expense_id = serializers.PrimaryKeyRelatedField(queryset=Expense.objects.all())

    deposite_type = serializers.CharField(default="other")
    expense_type = serializers.CharField(default="other")
    description = serializers.CharField(default="")

    class Meta:
        model = Transaction
        # fields = ['id', 'transaction_id', 'date', 'credit_amt', 'debit_amt', 'customer_id', 'deposit_type_id', 'expense_type_id']
        fields = '__all__'
        