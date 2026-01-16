"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from .views import CustomerUpdateView, CSVUploadAPI, CustomerAPI, CustomerLoginAPI, CustomerForgotPasswordAPI, CustomerVerifyOTPAPI, CustomerResetPasswordAPI
from . import views

# urlpatterns = [
#     path('', CustomerAPI.as_view(), name='root'),
#     path('customer/', views.CustomerAPI.as_view(), name='customer_api'),
#     path('<int:id>/', CustomerAPI.as_view(), name='customer_detail'), 
# ]


urlpatterns = [
    path('', CustomerAPI.as_view(), name='root'),
    path('customer/', views.CustomerAPI.as_view(), name='customer_api'),
    path('<int:id>/', CustomerAPI.as_view(), name='_detail'), 

    path('login/', CustomerLoginAPI.as_view(), name='login'),
    path('register/', views.CustomerAPI.as_view(), name='customer_api'),
    
    path('forgot-password/', CustomerForgotPasswordAPI.as_view()),
    path('verify-otp/', CustomerVerifyOTPAPI.as_view()),
    path('reset-password/', CustomerResetPasswordAPI.as_view()),

    path('upload-csv/', views.CSVUploadAPI.as_view(), name='upload_csv'),

    path('<int:customer_id>/image-upload/', views.CustomerUpdateView.as_view(), name='csvupload_api'),
    path('<int:customer_id>/image-upload/', views.CustomerUpdateView.as_view(), name='csvupload_api')

]


# urlpatterns = [
#     path('customers/', CustomerAPI.as_view()),
#     path('customers/<int:id>/', CustomerAPI.as_view()),
#     path('customers/login/', CustomerLoginAPI.as_view()),
#     # path('customers/telegram-link/', CustomerTelegramLinkTokenAPI.as_view()),
#     path('customers/forgot-password/', CustomerForgotPasswordAPI.as_view()),
#     path('customers/verify-otp/', CustomerVerifyOTPAPI.as_view()),
#     path('customers/reset-password/', CustomerResetPasswordAPI.as_view()),
# ]

