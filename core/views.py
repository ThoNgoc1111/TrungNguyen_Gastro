import json
import random
import string, requests

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import paypalrestsdk
from paypal.standard.forms import PayPalPaymentsForm
from rest_framework.views import APIView
from rest_framework.response import Response

import uuid
from .paypal import create_order, capture_order

from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, reverse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
import requests

from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm, ReviewForm, SupportTicketForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile, CATEGORY_CHOICES, Wishlist, WishlistItem, SupportTicket


paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def search(request):
    query = request.GET.get('query', '')
    results = Item.objects.filter(title__icontains=query) if query else []
    context = {
        'results': results,
        'query': query
    }
    return render(request, 'search.html', context) 

def add_to_wishlist(self, user):
        """Add this item to the user's wishlist."""
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        WishlistItem.objects.get_or_create(wishlist=wishlist, item=self)

def remove_from_wishlist(self, user):
    """Remove this item from the user's wishlist."""
    wishlist = Wishlist.objects.filter(user=user).first()
    if wishlist:
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, item=self).first()
        if wishlist_item:
            wishlist_item.delete()

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")

    def create_address(self, form, address_type):
        address1 = form.cleaned_data.get(f'{address_type}_address')
        address2 = form.cleaned_data.get(f'{address_type}_address2')
        country = form.cleaned_data.get(f'{address_type}_country')
        zip_code = form.cleaned_data.get(f'{address_type}_zip')

        if is_valid_form([address1, country, zip_code]):
            address = Address(
                user=self.request.user,
                street_address=address1,
                apartment_address=address2,
                country=country,
                zip=zip_code,
                address_type=address_type
            )
            address.save()
            return address
        else:
            messages.info(self.request, f"Please fill in the required {address_type} address fields")
            return None
    
        
        
class PaymentView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if order.billing_address:
                context = {
                    'order': order,
                    'DISPLAY_COUPON_FORM': False,
                    'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID
                }
                return render(self.request, 'payment.html', context)
            else:
                messages.warning(self.request, "No billing address found.")
                return redirect("/")  # Redirect if no billing address
        except Order.DoesNotExist:
            messages.warning(self.request, "You do not have an active order.")
            return redirect("/")  # Redirect if no order exists

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        
        if form.is_valid():
            # Create a PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": requests.request.build_absolute_uri(reverse('payment_completed')),
                    "cancel_url": requests.request.build_absolute_uri(reverse('payment_failed')),
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Order #{order.id}",
                            "sku": f"order-{order.id}",
                            "price": str(order.get_final_price()),  # Ensure price is a string
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "currency": "USD",
                        "total": str(order.get_final_price())  # Ensure total is a string
                    },
                    "description": f"Order #{order.id}"
                }]
            })

            if payment.create():
                # Save the payment ID for later use
                payment_id = payment.id
                # Redirect to PayPal for approval
                for link in payment.links:
                    if link.rel == "approval_url":
                        return redirect(link.href)
            else:
                messages.warning(self.request, "Error creating PayPal payment")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/")
    

@csrf_exempt
def paypal_ipn(request):
    if request.method == "POST":
        # Process the IPN payload
        payload = json.loads(request.body)
        # Handle the IPN message
        ipn_data = request.POST.copy()
        ipn_data['cmd'] = '_notify-validate'

        # Send the IPN data back to PayPal for validation
        response = requests.post(
            'https://api-m.sandbox.paypal.com/v2/checkout/orders/5FK24193D7608112C/capture',  # Use the sandbox URL for testing
            data=ipn_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        # Check if the response from PayPal is "VERIFIED"
        if response.text == "VERIFIED":
            # Process the payment
            # Here you can update the order status in your database
            # Example: 
            # order_id = ipn_data.get('invoice')  # Assuming you sent the order ID as 'invoice'
            # payment_status = ipn_data.get('payment_status')
            # Update your order in the database based on the order_id and payment_status

            # Log the IPN data for debugging
            print("IPN Verified:", ipn_data)

            return HttpResponse("IPN Verified", status=200)
        else:
            # Log the invalid response for debugging
            print("IPN Invalid:", response.text)
            return HttpResponse("IPN Invalid", status=400)

    return HttpResponse("Invalid Request", status=400)


def paypal_webhook(request):
    if request.method == "POST":
        payload = json.loads(request.body)
        event_type = payload["event_type"]

        if event_type == "payment.authorization.created":
            # Handle the authorization created event
            auth_id = payload["resource"]["id"]
            # ...
            return JsonResponse({"message": "Received and processed."}, status=200)

        elif event_type == "payment.authorization.voided":
            # Handle the authorization voided event
            auth_id = payload["resource"]["id"]
            # ...
            return JsonResponse({"message": "Received and processed."}, status=200)

        elif event_type == "payment.sale.completed":
            # Handle the sale completed event
            sale_id = payload["resource"]["id"]
            # ...
            return JsonResponse({"message": "Received and processed."}, status=200)

        else:
            return JsonResponse({"message": "Unhandled event type."}, status=400)

    else:
        return JsonResponse({"message": "Invalid request method."}, status=405)


@csrf_exempt
def payment_completed_view(request):
    return render(request, 'core/payment_completed.html')

def payment_failed_view(request):
    return render(request, 'core/payment_failed.html')



class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = CATEGORY_CHOICES  # Add CATEGORY_CHOICES to context
        return context
    
class CategoryView(ListView):
    model = Item
    template_name = "category.html"  # Create this template
    context_object_name = 'items'  # This will be the context variable for the items

    def get_queryset(self):
        category = self.kwargs['category']  # Get the category from the URL
        return Item.objects.filter(category=category)  # Filter items by category
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = CATEGORY_CHOICES
        return context

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "products.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()  # Get all reviews for the item
        context['review_form'] = ReviewForm()  # Initialize the review form
        context['support_ticket_form'] = SupportTicketForm()  # Initialize the support ticket form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Get the current product object
        
        # Handle review submission
        if 'review' in request.POST:
            return self.handle_review_submission(request)

        # Handle support ticket submission
        if 'support_ticket' in request.POST:
            return self.handle_support_ticket_submission(request)

        # If no valid form was submitted, re-render the page with the forms
        return self.get(request, *args, **kwargs)

    def handle_review_submission(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to be logged in to post a review. Login or Register an Account Now!")
            return redirect('core:product', slug=self.object.slug)  # Redirect to the same product page with the correct slug
        
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.item = self.object  # Associate with the product
            review.user = request.user  # Associate with the current user
            review.save()
            messages.success(request, "Your review has been submitted successfully.")
            return redirect('core:product', slug=self.object.slug)  # Redirect after saving
        else:
            messages.error(request, "There was an error submitting your review. Please correct the errors below or check if you are already logged in.")
            return self.get(request)  # Re-render with the invalid form

    def handle_support_ticket_submission(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to be logged in to submit a support ticket for this product. Login or Register an Account Now!")
            return redirect('core:product', slug=self.object.slug)  # Redirect to the same product page with the correct slug
        
        support_ticket_form = SupportTicketForm(request.POST)
        if support_ticket_form.is_valid():
            support_ticket = support_ticket_form.save(commit=False)
            support_ticket.item = self.object  # Associate with the product
            support_ticket.user = request.user  # Associate with the current user
            support_ticket.save()
            messages.success(request, "Your support ticket has been submitted successfully.")
            return redirect('core:product', slug=self.object.slug)  # Redirect after saving
        else:
            messages.error(request, "There was an error submitting your support ticket. Please correct the errors below or check if you are already logged in.")
            return self.get(request)  # Re-render with the invalid form


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:products", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")


class SupportTicketView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to log in to view this page.")
            return redirect('core:home')  # Redirect to the homepage or login page

        form = SupportTicketForm()
        return render(request, 'support_ticket.html', {'form': form})

    def post(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to log in to submit a support ticket.")
            return redirect('core:home')  # Redirect to the homepage or login page
        
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user  # Associate the ticket with the current user
            
            # Get the item slug from the form data
            item_slug = request.POST.get('item_slug')
            ticket.item = get_object_or_404(Item, slug=item_slug)  # Associate with the item
            ticket.save()


            # Prepare email content
            subject = f"New Support Ticket from {ticket.user.username}"
            message = f"""
            You have received a new support ticket.

            Subject: {ticket.subject}
            Message: {ticket.message}

            User: {ticket.user.username}
            Email: {ticket.user.email}
            """
            # Send email to the support team
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['admin@localhost'],  # Replace with your support team's email
                fail_silently=False,
            )

            # Send confirmation email to the user
            user_subject = "Support Ticket Submitted"
            user_message = f"""
            Hi {ticket.user.username},

            Thank you for reaching out to us. Your support ticket has been submitted successfully.

            Subject: {ticket.subject}
            Message: {ticket.message}

            We will get back to you shortly.

            Best regards,
            Your Company Name
            """
            send_mail(
                user_subject,
                user_message,
                settings.DEFAULT_FROM_EMAIL,
                [ticket.user.email],
                fail_silently=False,
            )

            messages.success(request, "Your support ticket has been submitted successfully. A confirmation email has been sent to you.")
            return redirect('core:product', slug=ticket.item.slug)  # Redirect to the product page with the slug

        # If the form is not valid, re-render the support ticket page with the form errors
        messages.error(request, "There was an error submitting your support ticket. Please correct the errors below.")
        return render(request, 'support_ticket.html', {'form': form})

class WishlistView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to be logged in to view your wishlist.")
            return redirect('core:product', slug=products.slug)  # Stay on the same products.html page

        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        context = {
            'wishlist_items': wishlist.items.all()
        }
        return render(request, 'wishlist.html', context)

class AddToWishlistView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to be logged in to modify your wishlist.")
            return redirect('core:product', slug=slug)  # Redirect to the product page or any other page you want

        item = get_object_or_404(Item, slug=slug)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        WishlistItem.objects.get_or_create(wishlist=wishlist, item=item)
        messages.success(request, f"{item.title} has been added to your wishlist.")
        return redirect('core:wishlist')

class RemoveFromWishlistView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            messages.warning(request, "You need to be logged in to modify your wishlist.")
            return redirect('core:product', slug=slug)  # Redirect to the product page or any other page you want

        item = get_object_or_404(Item, slug=slug)
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, item=item).first()
        if wishlist_item:
            wishlist_item.delete()
            messages.success(request, f"{item.title} has been removed from your wishlist.")
        return redirect('core:wishlist')
 
 
    
def start_payment(request):
    try:
        order = create_order(amount="100.00")
        approval_url = next(
            link["href"] for link in order["links"] if link["rel"] == "approve"
        )
        return HttpResponseRedirect(approval_url)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def capture_payment(request):
    order_id = request.GET.get("token")  # PayPal returns order_id as 'token'
    try:
        capture_response = capture_order(order_id)
        return JsonResponse(capture_response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)