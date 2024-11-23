from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stripe/', views.create_checkout_session, name='stripe-checkout'),
    path('sslcommerz/', views.sslcommerz_checkout, name='sslcommerz-checkout'),
    
    path('stripe/webhook/', views.stripe_webhook, name='stripe-webhook'),
    path('sslcommerz/webhook/', views.sslcommerz_webhook, name='sslcommerz-webhook'),
    
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('list/', views.payment_list, name='payment_list'),
]
