from django.http import JsonResponse
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
import uuid
import requests
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    if request.method == 'POST':
        # Get payment details from the form
        email = request.POST['email']
        base_amount = float(request.POST['amount'])
        vat_amount = float(request.POST.get('vat', 0))
        total_amount = int((base_amount + vat_amount) * 100)  # Convert to cents
        product_name = request.POST.get('product_name', 'Default Product')
        description = request.POST.get('description', '')

        # Create a checkout session with detailed line items
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['affirm', 'alipay', 'amazon_pay', 'card', 'cashapp', 'klarna', 'link', 'us_bank_account'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                        'description': description,
                        'metadata': {
                            'base_amount': str(base_amount),
                            'vat_amount': str(vat_amount)
                        }
                    },
                    'unit_amount': total_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
            metadata={
                'description': description,
                'email': email,
                'product_name': product_name,
                'base_amount': str(base_amount),
                'vat_amount': str(vat_amount),
                'total_amount': str(base_amount + vat_amount)
            }
        )
        return redirect(session.url)
    return render(request, 'payments/checkout.html')



@csrf_exempt
def stripe_webhook(request):
    print("stripe_webhook")
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    return JsonResponse({'status': 'success'})





def handle_successful_payment(session):
    amount_in_dollars = session.get('metadata').get('total_amount')
    product_name = session.get('metadata').get('product_name')
    customer_email = session.get('metadata').get('email')
    description = session.get('metadata').get('description')
    created = session.get('created')
    currency = session.get('currency')
    payment_status = session.get('payment_status')
    payment_intent_id = session.get('payment_intent')
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    latest_charge_id = payment_intent.latest_charge
    charge = stripe.Charge.retrieve(latest_charge_id)
    receipt_url = charge.receipt_url
    print(f"amount_in_dollars: {amount_in_dollars}")
    print(f"product_name: {product_name}")
    print(f"customer_email: {customer_email}")
    print(f"description: {description}")
    print(f"created: {created}")
    print(f"currency: {currency}")
    print(f"payment_status: {payment_status}")
    print(f"receipt_url: {receipt_url}")

    
    payment = Payment(
        amount=amount_in_dollars,
        amount_type="Dollars",
        product_name=product_name,
        customer_email=customer_email,
        description=description,
        created=int(timezone.now().timestamp()),
        updated=created,
        currency=currency,
        payment_status=payment_status,
        receipt_url=receipt_url
    )
    payment.save()
    




@csrf_exempt
def payment_success(request):
    return render(request, 'payments/success.html')

def payment_cancel(request):
    return render(request, 'payments/cancel.html')

def payment_list(request):
    payments = Payment.objects.all().order_by('-created')
    return render(request, 'payments/payment_list.html', {'payments': payments})

def home(request):
    return render(request, 'payments/home.html')

def sslcommerz_checkout(request):
    if request.method == 'POST':
        # Generate unique transaction ID
        tran_id = f"TX{uuid.uuid4().hex[:10]}"
        
        # Get form data
        post_data = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
            'total_amount': request.POST['amount'],
            'currency': "BDT",
            'tran_id': tran_id,
            'success_url': "http://localhost:8000/success/",
            'fail_url': "http://localhost:8000/cancel/",
            'cancel_url': "http://localhost:8000/cancel/",
            'ipn_url': 'https://bf76-103-209-109-230.ngrok-free.app/sslcommerz/webhook/',
            'cus_name': request.POST['name'],
            'cus_email': request.POST['email'],
            'cus_phone': request.POST['phone'],
            'cus_add1': request.POST['address'],
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'shipping_method': 'NO',
            'product_name': request.POST['product_name'],
            'product_category': 'General',
            'product_profile': 'general',
            
            'value_a': request.POST['email'],
            'value_b': request.POST['product_name'],
            'value_c': request.POST['description'],
        }

        # Create payment record
        payment = Payment(
            customer_email=post_data['value_a'],
            product_name=post_data['value_b'],
            description=post_data['value_c'],
            amount=float(post_data['total_amount']),
            amount_type="Taka",
            currency='BDT',
            payment_status='PENDING',
            created=int(timezone.now().timestamp()),
        )
        payment.save()

        # Make API request to SSLCommerz
        response = requests.post(settings.SSLCOMMERZ_API_URL, data=post_data)
        data = response.json()

        if data['status'] == 'SUCCESS':
            return redirect(data['GatewayPageURL'])
        else:
            return JsonResponse({
                'error': 'Payment initiation failed',
                'message': data.get('failedreason', 'Unknown error')
            }, status=400)

    return render(request, 'payments/sslcommerz_checkout.html')

@csrf_exempt
def sslcommerz_webhook(request):
    print("sslcommerz_webhook")
    if request.method == 'POST':
        payment_data = request.POST
        
        # Validate the payment
        validation_data = {
            'val_id': payment_data.get('val_id', ''),
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        }
        
        validation_response = requests.get(
            settings.SSLCOMMERZ_VALIDATION_URL,
            params=validation_data
        )
        
        if validation_response.json()['status'] == 'VALID':
            # Update payment record
            try:
                payment = Payment.objects.get(
                    customer_email=payment_data.get('value_a'),
                    product_name=payment_data.get('value_b'),
                    amount=validation_response.json()['amount'],
                    amount_type="Taka",
                    currency='BDT',
                    payment_status='PENDING',
                )
                payment.payment_status = "paid"
                payment.updated = int(timezone.now().timestamp())
                # payment.receipt_url = 
                payment.save()
            except Payment.DoesNotExist:
                pass
                
        return JsonResponse({'status': 'Success'})
        
    return JsonResponse({'status': 'Failed'}, status=400)



