
# class Customer(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = models.CharField(max_length= 10)
#     address = models.TextField(blank = True)
#     created_at = models.DateTimeField(auto_now_add = True)

#     def __str__(self):
#         return self.name



from django.db import models
from django import forms
from django.utils import timezone
import uuid


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length= 10)
    password = models.TextField(max_length=220, default='')
    reset_token = models.CharField(max_length=512, blank=True, null=True)
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)

    # Store profile image as Base64 string
    profile_image_base64 = models.TextField(blank=True, null=True)
    
    type = models.CharField(max_length=50, default='')
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.name
    


class CustomerPasswordResetOTP(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reset_otps')
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)    # OTP verified
    is_used = models.BooleanField(default=False)        # reset completed
    reset_token = models.CharField(max_length=64, blank=True, null=True)  # returned after verify
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at
