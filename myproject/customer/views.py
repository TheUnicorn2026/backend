import random
from datetime import timedelta

import csv
from rest_framework.parsers import MultiPartParser, FormParser

import requests
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Customer, CustomerPasswordResetOTP
from .serializer import CustomerSerializer


OTP_EXP_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


# --------------------------------------------------
# PROFILE UPLOAD
# --------------------------------------------------
class CustomerUpdateView(APIView):
    def post(self, request, *args, **kwargs):
        # Look up the customer using their ID or email
        customer_id = kwargs.get('customer_id')  # Or use request.data.get('email') if searching by email
        customer = Customer.objects.filter(id=customer_id).first()  # You can also filter by email if needed

        if not customer:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if base64 image is provided in the request
        base64_image = request.data.get('profile_image_base64')
        if base64_image:
            customer.profile_image_base64 = base64_image
            customer.save()

            return Response({'success': True, 'status': 'Profile image updated successfully'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
            # Look up the customer using their ID
            customer_id = kwargs.get('customer_id')
            customer = Customer.objects.filter(id=customer_id).first()

            if not customer:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if customer has an image (Base64-encoded or file)
            if customer.profile_image_base64:
                return Response({'profile_image_base64': customer.profile_image_base64}, status=status.HTTP_200_OK)
            
            # If no image is available
            return Response({'error': 'No profile image found'}, status=status.HTTP_404_NOT_FOUND)



# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------
class CSVUploadAPI(APIView):
    parser_classes = [MultiPartParser, FormParser]  # Allow file uploads via form-data
    
    def post(self, request):
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            return Response({"error": "csv_file is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read the CSV file
        try:
            data = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(data)
            next(reader)  # Skip header row

            # Loop through each row in the CSV and create Customer instances
            for row in reader:
                if len(row) >= 6:  # Ensure that the CSV row has the expected number of columns
                    customer_data = {
                        'name': row[0],
                        'email': row[1],
                        'phone': row[2],
                        'password': make_password(row[3]),  # Ideally, you should hash passwords before saving
                        'type': row[4],
                        'telegram_chat_id': row[5] if len(row) > 5 else '',
                    }

                    print(customer_data)
                    # Create customer instance using the serializer
                    serializer = CustomerSerializer(data=customer_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"message": "CSV uploaded and customers created successfully."}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



# --------------------------------------------------
# CUSTOMER CRUD
# --------------------------------------------------
class CustomerAPI(APIView):

    def post(self, request):
        data = request.data.copy()
        if data.get('password') :
            data['password'] = make_password(data['password'])
        else:
            data['password'] = "admin"

        serializer = CustomerSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        if id:
            try:
                customer = Customer.objects.get(id=id)
            except Customer.DoesNotExist:
                return Response({"error": "Not Found"}, status=404)

            return Response(CustomerSerializer(customer).data)

        customers = Customer.objects.all()
        return Response(CustomerSerializer(customers, many=True).data)

    def put(self, request, id):
        try:
            customer = Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)

        data = request.data.copy()
        if data.get("password"):
            data["password"] = make_password(data["password"])

        serializer = CustomerSerializer(customer, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        try:
            customer = Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return Response({"error": "Not Found"}, status=404)

        customer.delete()
        return Response({"message": "Customer Deleted"}, status=204)


# --------------------------------------------------
# CUSTOMER LOGIN
# --------------------------------------------------
class CustomerLoginAPI(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        try:
            customer = Customer.objects.get(email=email)

            if check_password(password, customer.password):
                refresh = RefreshToken.for_user(customer)

                return Response({
                    "message": "Login successful",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "customer": CustomerSerializer(customer).data
                })

            return Response({"error": "Invalid credentials"}, status=400)

        except Customer.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=400)


# --------------------------------------------------
# TELEGRAM MESSAGE HELPER
# --------------------------------------------------
def send_telegram_message(chat_id, text):
    TELEGRAM_BOT_TOKEN = "8356288691:AAFneoqDVHxF88rrFLNXbx-6ucoRVWiumm4"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        return requests.post(url, json=payload, timeout=5).ok
    except Exception:
        return False


# --------------------------------------------------
# FORGOT PASSWORD → SEND OTP
# --------------------------------------------------
class CustomerForgotPasswordAPI(APIView):

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "email required"}, status=400)

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            return Response({"message": "If account exists, OTP sent"})

        if not customer.telegram_chat_id:
            return Response({"error": "Telegram not linked"}, status=400)

        otp = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=OTP_EXP_MINUTES)

        CustomerPasswordResetOTP.objects.create(
            customer=customer,
            otp=otp,
            expires_at=expires_at
        )

        send_telegram_message(
            customer.telegram_chat_id,
            f"🔐 OTP: {otp} (valid {OTP_EXP_MINUTES} minutes)"
        )

        return Response({"message": "If account exists, OTP sent"})


# --------------------------------------------------
# VERIFY OTP
# --------------------------------------------------
class CustomerVerifyOTPAPI(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response(
                {"error": "email and otp required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            customer = Customer.objects.get(email=email)
            reset = CustomerPasswordResetOTP.objects.filter(
                customer=customer
            ).latest('created_at')
        except (Customer.DoesNotExist, CustomerPasswordResetOTP.DoesNotExist):
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset.is_used or reset.is_expired():
            return Response(
                {"error": "OTP expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset.otp != otp:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = AccessToken.for_user(customer)
        token['purpose'] = 'password_reset'

        reset.reset_token = str(token)
        reset.is_verified = True
        reset.is_used = False
        reset.save()

        return Response(
            {"reset_token": str(token)},
            status=status.HTTP_200_OK
        )


# --------------------------------------------------
# RESET PASSWORD
# --------------------------------------------------
class CustomerResetPasswordAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")

        print(email, new_password, reset_token)
        if not email or not reset_token or not new_password:
            return Response({"error": "missing fields"}, status=400)

        try:
            token = AccessToken(reset_token)
            if token.get("purpose") != "password_reset":
                raise TokenError()
        except TokenError:
            return Response({"error": "Invalid token"}, status=400)

        try:
            customer = Customer.objects.get(id=token["user_id"], email=email)
            reset = CustomerPasswordResetOTP.objects.get(
                customer=customer,
                reset_token=reset_token,
                is_verified=True,
                is_used=False
            )
        except Exception:
            return Response({"error": "Invalid token"}, status=400)

        customer.password = make_password(new_password)
        customer.save()

        reset.is_used = True
        reset.save()

        send_telegram_message(
            customer.telegram_chat_id,
            "✅ Password changed successfully"
        )

        return Response({"message": "Password reset successful"})
