from django.http import JsonResponse
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Payment

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
        amount_in_dollars=amount_in_dollars,
        product_name=product_name,
        customer_email=customer_email,
        description=description,
        created=created,
        currency=currency,
        payment_status=payment_status,
        receipt_url=receipt_url
    )
    payment.save()
    




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
    # Implement SSLCommerz checkout logic here
    return render(request, 'payments/checkout.html')





@csrf_exempt
def sslcommerz_webhook(request):
    # Implement SSLCommerz webhook logic here
    return JsonResponse({'status': 'success'})



