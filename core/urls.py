from django.urls import path
from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    CategoryView, 
    search,
    SupportTicketView,
    WishlistView,
    AddToWishlistView, 
    RemoveFromWishlistView,
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('category/<str:category>/', CategoryView.as_view(), name='category-view'),
    path('search/', search, name='search'),
    path('support-ticket/', SupportTicketView.as_view(), name='support_ticket'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('add-to-wishlist/<slug:slug>/', AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('remove-from-wishlist/<slug:slug>/', RemoveFromWishlistView.as_view(), name='remove_from_wishlist'),
]
