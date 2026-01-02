from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from .forms import ExtraPaymentForm, LeaseForm, MoneyTransactionForm, PaymentForm, RentRateForm
from .models import ExtraPayment, Lease, MoneyTransaction, Payment, RentRate


@require_http_methods(["GET"])
def lease_list(request: HttpRequest) -> HttpResponse:
    queryset = Lease.objects.all()

    # Search
    search = request.GET.get("search")
    if search:
        search = search.strip()
        filters = Q(title__icontains=search)
        if search.isdigit():
            filters |= Q(id=int(search))
        queryset = queryset.filter(filters)

    # Filters
    # Note: In a real app, you might want to use a Form to handle this validation gracefully
    try:
        if before := request.GET.get("first_period_start_before"):
            queryset = queryset.filter(first_period_start__lte=before)
        if after := request.GET.get("first_period_start_after"):
            queryset = queryset.filter(first_period_start__gte=after)
    except ValueError:
        pass  # Ignore invalid dates for now

    # Ordering
    ordering = request.GET.get("ordering", "-first_period_start")
    allowed_ordering = {
        "id",
        "title",
        "first_period_start",
        "currency",
        "-id",
        "-title",
        "-first_period_start",
        "-currency",
    }
    if ordering not in allowed_ordering:
        ordering = "-first_period_start"

    leases = queryset.order_by(ordering)

    context = {
        "leases": leases,
        "search": search or "",
    }
    return render(request, "leases/lease_list.html", context)


@require_http_methods(["GET", "POST"])
def lease_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = LeaseForm(request.POST)
        if form.is_valid():
            lease = form.save()
            messages.success(request, f"Lease '{lease}' created successfully.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = LeaseForm()

    return render(request, "leases/lease_form.html", {"form": form, "action": "Create"})


@require_http_methods(["GET"])
def lease_detail(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(
        Lease.objects.prefetch_related("rent_rates", "payments", "extra_payments", "money_transactions"), pk=lease_id
    )

    # Data for JS payment suggestion
    current_rate = lease.rent_rates.filter(end_date__isnull=True).first()
    last_payment = lease.payments.order_by("-target_period_start").first()
    last_period = None
    if last_payment and last_payment.target_period_start:
        last_period = last_payment.target_period_start.isoformat()

    # Data for JS payment suggestions
    js_data = {
        "leaseStart": lease.first_period_start.isoformat(),
        "lastPeriod": last_period,
        "currentRate": str(current_rate.amount) if current_rate else None,
        "quickCreateUrl": f"/leases/{lease.pk}/payments/quick-create/",
        "csrfToken": get_token(request),
        "labels": {
            "overdue": _("Overdue"),
            "planned": _("Planned"),
            "add": _("Add"),
            "for": _("for"),
        },
    }

    # Calculate payment totals
    payments = lease.payments.all()
    payments_total = sum(p.amount for p in payments)

    # Group by year (using target_period_start or date)
    from collections import defaultdict
    from decimal import Decimal

    yearly_totals = defaultdict(Decimal)
    for p in payments:
        year = (p.target_period_start or p.date).year
        yearly_totals[year] += p.amount
    # Sort by year descending
    yearly_totals = sorted(yearly_totals.items(), reverse=True)

    context = {
        "lease": lease,
        "rent_rates": lease.rent_rates.all(),
        "payments": payments,
        "payments_total": payments_total,
        "payments_yearly": yearly_totals,
        "extra_payments": lease.extra_payments.all(),
        "transactions": lease.money_transactions.all(),
        "js_data": js_data,
    }
    return render(request, "leases/lease_detail.html", context)


@require_http_methods(["GET", "POST"])
def lease_update(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)

    if request.method == "POST":
        form = LeaseForm(request.POST, instance=lease)
        if form.is_valid():
            form.save()
            messages.success(request, "Lease updated.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = LeaseForm(instance=lease)

    return render(request, "leases/lease_form.html", {"form": form, "action": "Update", "lease": lease})


@require_http_methods(["POST"])
def lease_delete(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    lease.delete()
    messages.success(request, "Lease deleted.")
    return redirect("leases:lease_list")


# RentRate views


@require_http_methods(["GET", "POST"])
def rent_rate_create(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)

    if request.method == "POST":
        form = RentRateForm(request.POST)
        if form.is_valid():
            rent_rate = form.save(commit=False)
            rent_rate.lease = lease

            # Close previous open rate (one day before new rate starts)
            previous_rate = lease.rent_rates.filter(end_date__isnull=True).first()
            if previous_rate:
                previous_rate.end_date = rent_rate.effective_date - timedelta(days=1)
                previous_rate.save()

            rent_rate.save()
            messages.success(request, "Rent rate created.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = RentRateForm()

    return render(
        request,
        "leases/rent_rate_form.html",
        {
            "form": form,
            "lease": lease,
            "action": "Create",
        },
    )


@require_http_methods(["GET", "POST"])
def rent_rate_update(request: HttpRequest, lease_id: int, rate_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    rent_rate = get_object_or_404(RentRate, pk=rate_id, lease=lease)

    if request.method == "POST":
        form = RentRateForm(request.POST, instance=rent_rate)
        if form.is_valid():
            form.save()
            messages.success(request, "Rent rate updated.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = RentRateForm(instance=rent_rate)

    return render(
        request,
        "leases/rent_rate_form.html",
        {
            "form": form,
            "lease": lease,
            "rent_rate": rent_rate,
            "action": "Update",
        },
    )


@require_http_methods(["POST"])
def rent_rate_delete(request: HttpRequest, lease_id: int, rate_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    rent_rate = get_object_or_404(RentRate, pk=rate_id, lease=lease)
    rent_rate.delete()
    messages.success(request, "Rent rate deleted.")
    return redirect("leases:lease_detail", lease_id=lease.pk)


# Payment views


@require_http_methods(["GET", "POST"])
def payment_create(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.lease = lease
            payment.save()
            messages.success(request, "Payment created.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = PaymentForm()

    return render(
        request,
        "leases/payment_form.html",
        {
            "form": form,
            "lease": lease,
            "action": "Create",
        },
    )


@require_http_methods(["GET", "POST"])
def payment_update(request: HttpRequest, lease_id: int, payment_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    payment = get_object_or_404(Payment, pk=payment_id, lease=lease)

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment updated.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = PaymentForm(instance=payment)

    return render(
        request,
        "leases/payment_form.html",
        {
            "form": form,
            "lease": lease,
            "payment": payment,
            "action": "Update",
        },
    )


@require_http_methods(["POST"])
def payment_delete(request: HttpRequest, lease_id: int, payment_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    payment = get_object_or_404(Payment, pk=payment_id, lease=lease)
    payment.delete()
    messages.success(request, "Payment deleted.")
    return redirect("leases:lease_detail", lease_id=lease.pk)


@require_http_methods(["POST"])
def payment_quick_create(request: HttpRequest, lease_id: int) -> HttpResponse:
    """Create a suggested payment with one click (data from JS)."""
    from django.http import JsonResponse

    lease = get_object_or_404(Lease, pk=lease_id)
    current_rate = lease.rent_rates.filter(end_date__isnull=True).first()

    if not current_rate:
        return JsonResponse({"error": "No active rent rate"}, status=400)

    # Get data from POST
    status = request.POST.get("status", Payment.Status.PLANNED)
    target_period = request.POST.get("target_period_start")

    if status not in [s.value for s in Payment.Status]:
        status = Payment.Status.PLANNED

    Payment.objects.create(
        lease=lease,
        date=date.today(),
        amount=current_rate.amount,
        status=status,
        target_period_start=target_period,
    )
    return JsonResponse({"success": True})


# ExtraPayment views


@require_http_methods(["GET", "POST"])
def extra_payment_create(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)

    if request.method == "POST":
        form = ExtraPaymentForm(request.POST)
        if form.is_valid():
            extra_payment = form.save(commit=False)
            extra_payment.lease = lease
            extra_payment.save()
            messages.success(request, "Extra payment created.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = ExtraPaymentForm()

    return render(
        request,
        "leases/extra_payment_form.html",
        {
            "form": form,
            "lease": lease,
            "action": "Create",
        },
    )


@require_http_methods(["GET", "POST"])
def extra_payment_update(request: HttpRequest, lease_id: int, extra_payment_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    extra_payment = get_object_or_404(ExtraPayment, pk=extra_payment_id, lease=lease)

    if request.method == "POST":
        form = ExtraPaymentForm(request.POST, instance=extra_payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Extra payment updated.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = ExtraPaymentForm(instance=extra_payment)

    return render(
        request,
        "leases/extra_payment_form.html",
        {
            "form": form,
            "lease": lease,
            "extra_payment": extra_payment,
            "action": "Update",
        },
    )


@require_http_methods(["POST"])
def extra_payment_delete(request: HttpRequest, lease_id: int, extra_payment_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    extra_payment = get_object_or_404(ExtraPayment, pk=extra_payment_id, lease=lease)
    extra_payment.delete()
    messages.success(request, "Extra payment deleted.")
    return redirect("leases:lease_detail", lease_id=lease.pk)


# MoneyTransaction views


@require_http_methods(["GET", "POST"])
def transaction_create(request: HttpRequest, lease_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)

    if request.method == "POST":
        form = MoneyTransactionForm(request.POST, lease=lease)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.lease = lease
            transaction.save()
            form.save_m2m()  # Save ManyToMany relationships
            messages.success(request, "Transaction created.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = MoneyTransactionForm(lease=lease)

    return render(
        request,
        "leases/transaction_form.html",
        {
            "form": form,
            "lease": lease,
            "action": "Create",
        },
    )


@require_http_methods(["GET", "POST"])
def transaction_update(request: HttpRequest, lease_id: int, transaction_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    transaction = get_object_or_404(MoneyTransaction, pk=transaction_id, lease=lease)

    if request.method == "POST":
        form = MoneyTransactionForm(request.POST, instance=transaction, lease=lease)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated.")
            return redirect("leases:lease_detail", lease_id=lease.pk)
    else:
        form = MoneyTransactionForm(instance=transaction, lease=lease)

    return render(
        request,
        "leases/transaction_form.html",
        {
            "form": form,
            "lease": lease,
            "transaction": transaction,
            "action": "Update",
        },
    )


@require_http_methods(["POST"])
def transaction_delete(request: HttpRequest, lease_id: int, transaction_id: int) -> HttpResponse:
    lease = get_object_or_404(Lease, pk=lease_id)
    transaction = get_object_or_404(MoneyTransaction, pk=transaction_id, lease=lease)
    transaction.delete()
    messages.success(request, "Transaction deleted.")
    return redirect("leases:lease_detail", lease_id=lease.pk)
