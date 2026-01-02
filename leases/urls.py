from django.urls import path

from . import views

app_name = "leases"

urlpatterns = [
    path("", views.lease_list, name="lease_list"),
    path("create/", views.lease_create, name="lease_create"),
    path("<int:lease_id>/", views.lease_detail, name="lease_detail"),
    path("<int:lease_id>/edit/", views.lease_update, name="lease_update"),
    path("<int:lease_id>/delete/", views.lease_delete, name="lease_delete"),
    # RentRate
    path("<int:lease_id>/rates/create/", views.rent_rate_create, name="rent_rate_create"),
    path("<int:lease_id>/rates/<int:rate_id>/edit/", views.rent_rate_update, name="rent_rate_update"),
    path("<int:lease_id>/rates/<int:rate_id>/delete/", views.rent_rate_delete, name="rent_rate_delete"),
    # Payment
    path("<int:lease_id>/payments/create/", views.payment_create, name="payment_create"),
    path("<int:lease_id>/payments/quick-create/", views.payment_quick_create, name="payment_quick_create"),
    path("<int:lease_id>/payments/<int:payment_id>/edit/", views.payment_update, name="payment_update"),
    path("<int:lease_id>/payments/<int:payment_id>/delete/", views.payment_delete, name="payment_delete"),
    # ExtraPayment
    path("<int:lease_id>/extra-payments/create/", views.extra_payment_create, name="extra_payment_create"),
    path(
        "<int:lease_id>/extra-payments/<int:extra_payment_id>/edit/",
        views.extra_payment_update,
        name="extra_payment_update",
    ),
    path(
        "<int:lease_id>/extra-payments/<int:extra_payment_id>/delete/",
        views.extra_payment_delete,
        name="extra_payment_delete",
    ),
    # MoneyTransaction
    path("<int:lease_id>/transactions/create/", views.transaction_create, name="transaction_create"),
    path("<int:lease_id>/transactions/<int:transaction_id>/edit/", views.transaction_update, name="transaction_update"),
    path(
        "<int:lease_id>/transactions/<int:transaction_id>/delete/", views.transaction_delete, name="transaction_delete"
    ),
]
