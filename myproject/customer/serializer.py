# from rest_framework import serializers
# from .models import Customer

# class CustomerSerializer(serializers.ModelSerializer):
#     name = serializers.CharField(max_length=100)
#     email = serializers.EmailField()
#     phone = serializers.CharField(max_length=10)
#     address = serializers.CharField(  # Keeping this as CharField
#         allow_blank=True,  # This allows blank addresses
#         max_length=500  # Optional: Limit the address to a certain number of characters
#     )
#     created_at = serializers.DateTimeField(read_only=True)  # Mark it as read-only

#     class Meta:
#         model = Customer
#         fields = '__all__'





from rest_framework import serializers
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_at',)

