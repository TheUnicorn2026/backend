import random
import uuid
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError


from .models import User, PasswordResetOTP
from .serializer import UserSerializer


OTP_EXP_MINUTES = 5
MAX_OTP_ATTEMPTS = 5

# Create your views here.


class UserAPI(APIView):

    def post(self, request):
        data = request.data.copy()
        data['password'] = make_password(data['password'])

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        if id:
            try:
                # permission_classes = [IsAuthenticated]
                user = User.objects.get(id=id)  # Corrected to .objects
            except User.DoesNotExist:
                return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = UserSerializer(user)
            return Response(serializer.data)

        users = User.objects.all()  # Corrected to .objects
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def put(self, request, id):
        if id:
            try:
                user = User.objects.get(id=id)  # Corrected to .objects
            except User.DoesNotExist:  # Corrected exception type
                return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = UserSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"message": "Customer Deleted"}, status=status.HTTP_204_NO_CONTENT)
    

class LoginAPI(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            
            # if password == serializer.data.password:
            if password == user.password or check_password(password, user.password):
                refresh = RefreshToken.for_user(user)

                return Response(
                    {
                        "message": "Login successful",
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            else: 
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        

def send_telegram_message(chat_id, text):
    TELEGRAM_BOT_TOKEN = "8356288691:AAFneoqDVHxF88rrFLNXbx-6ucoRVWiumm4"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.ok:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message. Response code: {response.status_code}, Response text: {response.text}")
            return False
    except Exception as e:
        print(f"Error occurred while sending message: {e}")
        return False


class TelegramLinkTokenAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        token = uuid.uuid4().hex
        user.reset_token = token
        user.save()

        return Response({
            "message": "Send this to Telegram bot",
            "telegram_command": f"/start {token}"
        })



class ForgotPasswordAPI(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"error": "email required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # do NOT reveal user existence
            return Response(
                {"message": "If account exists, OTP sent"},
                status=status.HTTP_200_OK
            )

        if not user.telegram_chat_id:
            return Response(
                {"error": "Telegram not linked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = f"{random.randint(0, 999999):06d}"
        expires_at = timezone.now() + timedelta(minutes=5)

        PasswordResetOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at
        )

        send_telegram_message(
            user.telegram_chat_id,
            f"Password reset OTP: {otp}\nValid for 5 minutes."
        )

        return Response(
            {"message": "If account exists, OTP sent"},
            status=status.HTTP_200_OK
        )


class VerifyOTPAPI(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response(
                {"error": "email and otp required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            reset = PasswordResetOTP.objects.filter(user=user).latest('created_at')
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if reset.is_used or reset.is_expired():
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        if reset.otp != otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        token = AccessToken.for_user(user)
        token['purpose'] = 'password_reset'
        # token.set_exp(from_time=timezone.now(), lifetime=timedelta(minutes=5))
        token = AccessToken.for_user(user)
        token['purpose'] = 'password_reset'


        reset.reset_token = str(token)   # store JWT string so DB and request can be correlated
        reset.is_verified = True
        reset.is_used = False
        reset.save()

        return Response(
            {"reset_token": str(token)},
            status=status.HTTP_200_OK
        )



class ResetPasswordAPI(APIView):
    authentication_classes = []  # 🔑 disable DRF auth
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        reset_token = request.data.get('reset_token')
        new_password = request.data.get('new_password')

        if not email or not reset_token or not new_password:
            return Response(
                {"error": "email, token, password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Decode token manually
        try:
            token = AccessToken(reset_token)
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=400)

        # 2. Validate purpose
        if token.get('purpose') != 'password_reset':
            return Response({"error": "Invalid token purpose"}, status=401)

        # 3. Get user from token
        user_id = token.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # 4. Email safety check
        if user.email != email:
            return Response({"error": "Email does not match token"}, status=400)

        # 5. Validate OTP record
        try:
            reset = PasswordResetOTP.objects.get(
                user=user,
                reset_token=reset_token,
                is_verified=True,
                is_used=False
            )
        except PasswordResetOTP.DoesNotExist:
            return Response({"error": "Invalid or already-used token"}, status=400)

        # 6. Reset password
        user.password = make_password(new_password)
        user.save()

        reset.is_used = True
        reset.save()

        send_telegram_message(
            user.telegram_chat_id,
            "✅ Your password has been changed successfully."
        )

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )
    
        try:
            jwt_auth = JWTAuthentication()
            try:
                user_auth, validated_token = jwt_auth.authenticate(request)
            except AuthenticationFailed:
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

            if validated_token.get('purpose') != 'password_reset':
                return Response({"error": "Invalid token purpose"}, status=status.HTTP_401_UNAUTHORIZED)

            user = user_auth  # user object authenticated from the JWT

            # Optional: ensure the email in body matches JWT user (safer)
            if email and user.email != email:
                return Response({"error": "Email does not match token"}, status=status.HTTP_400_BAD_REQUEST)

            # find the OTP row that holds this reset_token
            reset = PasswordResetOTP.objects.get(
                user=user,
                reset_token=reset_token,
                is_verified=True,
                is_used=False
            )

        except (PasswordResetOTP.DoesNotExist):
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()

        reset.is_used = True
        reset.save()

        send_telegram_message(
            user.telegram_chat_id,
            "✅ Your password has been changed successfully."
        )

        return Response(
            {"message": "Password reset successful"},
            status=status.HTTP_200_OK
        )




