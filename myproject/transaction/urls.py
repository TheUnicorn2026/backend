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
from .views import TransactionAPI, CSVUploadAPI
from . import views

urlpatterns = [
    path('', TransactionAPI.as_view(), name='root'),
    path('transaction/', views.TransactionAPI.as_view(), name='transaction_api'),
    # path('<int:id>/', TransactionAPI.as_view(), name='transaction_detail'), 
    path('transactions/<int:customer_id>/', views.TransactionAPI.as_view()),

    path('upload/', views.CSVUploadAPI.as_view(), name='csvupload_api'),


# wrong =>
    # path('', views.get, name='CustomerAPI'),
    # path("customer", views.get, name="customer"),
    # path("", views.get, name="customer"),
]
