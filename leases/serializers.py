from __future__ import annotations

from typing import Any

from .models import ExtraPayment, Lease, MoneyTransaction, Payment, RentRate

CURRENCY_SYMBOL = {
    "RUB": "₽",
    "USD": "$",
    "EUR": "€",
}


def serialize_lease_summary(lease: Lease) -> dict[str, Any]:
    return {
        "id": lease.id,
        "title": lease.title,
        "first_period_start": lease.first_period_start.isoformat(),
        "currency": lease.currency,
        "currency_symbol": CURRENCY_SYMBOL.get(lease.currency, lease.currency),
        "notes": getattr(lease, "notes", ""),
    }


def serialize_rent_rate(rate: RentRate) -> dict[str, Any]:
    return {
        "id": rate.id,
        "amount": str(rate.amount),
        "effective_date": rate.effective_date.isoformat(),
        "end_date": rate.end_date.isoformat() if rate.end_date else None,
        "notes": rate.notes,
    }


def serialize_payment(payment: Payment) -> dict[str, Any]:
    data = {
        "id": payment.id,
        "date": payment.date.isoformat(),
        "amount": str(payment.amount),
        "status": payment.status,
        "status_label": payment.get_status_display(),
        "target_period_start": payment.target_period_start.isoformat() if payment.target_period_start else None,
        "notes": payment.notes,
    }
    return data


def serialize_extra_payment(extra: ExtraPayment) -> dict[str, Any]:
    return {
        "id": extra.id,
        "title": extra.title,
        "description": extra.description,
        "direction": extra.direction,
        "direction_label": extra.get_direction_display(),
        "status": extra.status,
        "status_label": extra.get_status_display(),
        "agreed_date": extra.agreed_date.isoformat(),
        "paid_date": extra.paid_date.isoformat() if extra.paid_date else None,
        "amount": str(extra.amount),
    }


def serialize_money_transaction(transaction: MoneyTransaction) -> dict[str, Any]:
    return {
        "id": transaction.id,
        "date": transaction.date.isoformat(),
        "amount": str(transaction.amount),
        "notes": transaction.notes,
        "payment_ids": list(transaction.payments_covered.values_list("id", flat=True)),
        "extra_payment_ids": list(transaction.extra_payments_covered.values_list("id", flat=True)),
        "created_at": transaction.created_at.isoformat(),
        "updated_at": transaction.updated_at.isoformat(),
    }
