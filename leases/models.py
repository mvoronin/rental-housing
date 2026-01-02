from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class RentPeriod:
    """Represents a single monthly rent period."""

    start: date
    end: date
    amount: Decimal


class Lease(models.Model):
    """Represents the agreement under which rent is paid."""

    class Currency(models.TextChoices):
        RUB = "RUB", _("Russian ruble")
        USD = "USD", _("US dollar")
        EUR = "EUR", _("Euro")

    title = models.CharField(_("Title"), max_length=255, blank=True)
    first_period_start = models.DateField(_("First period start"), help_text=_("Date when the lease starts."))
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        help_text=_("All rent rates and payments for this lease are in this currency."),
    )

    class Meta:
        ordering = ("-first_period_start", "id")
        verbose_name = _("Lease")
        verbose_name_plural = _("Leases")

    def __str__(self) -> str:
        return self.title or _("Lease starting %(date)s") % {"date": self.first_period_start.strftime("%Y-%m-%d")}


class RentRate(models.Model):
    """Historical record of rent costs for a lease."""

    lease = models.ForeignKey(Lease, related_name="rent_rates", on_delete=models.CASCADE, verbose_name=_("Lease"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2, help_text=_("Monthly rent amount."))
    effective_date = models.DateField(_("Effective from"), help_text=_("Date when this rent amount starts applying."))
    end_date = models.DateField(
        _("Effective until"),
        null=True,
        blank=True,
        help_text=_("Date when this amount stops applying (exclusive). Leave empty for the current rate."),
    )
    notes = models.CharField(_("Notes"), max_length=255, blank=True)

    class Meta:
        ordering = ("effective_date", "id")
        verbose_name = _("Rent rate")
        verbose_name_plural = _("Rent rates")
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__isnull=True) | models.Q(end_date__gt=models.F("effective_date")),
                name="rent_rate_end_after_start",
            )
        ]

    def __str__(self) -> str:
        label = _("%(amount)s starting %(start)s") % {
            "amount": self.amount,
            "start": self.effective_date.strftime("%Y-%m-%d"),
        }
        if self.end_date:
            label = _("%(label)s until %(end)s") % {
                "label": label,
                "end": self.end_date.strftime("%Y-%m-%d"),
            }
        return label


class Payment(models.Model):
    """Tracks rent payments related to the lease (rent-only)."""

    class Status(models.TextChoices):
        PLANNED = "planned", _("Planned payment")
        OVERDUE = "overdue", _("Overdue payment")
        RESERVED = "reserved", _("Reserved for landlord")
        PAID = "paid", _("Paid to landlord")

    lease = models.ForeignKey(Lease, related_name="payments", on_delete=models.CASCADE, verbose_name=_("Lease"))
    date = models.DateField(_("Date"), help_text=_("Date when the money moved or is expected to move."))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    status = models.CharField(_("Status"), max_length=20, choices=Status.choices, default=Status.PAID)
    target_period_start = models.DateField(
        _("Target period start"),
        null=True,
        blank=True,
        help_text=_("Optional rent period this payment is linked to (start date)."),
    )
    notes = models.CharField(_("Notes"), max_length=255, blank=True)

    class Meta:
        ordering = ("-date", "id")
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self) -> str:
        return _("%(amount)s on %(date)s (%(status)s)") % {
            "amount": self.amount,
            "date": self.date.strftime("%Y-%m-%d"),
            "status": self.get_status_display(),
        }


class ExtraPayment(models.Model):
    """
    Non-rent payment tied to a lease: compensations, refunds, purchases, etc.
    Amount is always positive; direction defines who pays whom.
    Excluded from rent balance.
    """

    class Direction(models.TextChoices):
        TENANT_TO_LANDLORD = "tenant_to_landlord", _("Tenant to landlord")
        LANDLORD_TO_TENANT = "landlord_to_tenant", _("Landlord to tenant")

    class Status(models.TextChoices):
        PLANNED = "planned", _("Planned payment")
        RESERVED = "reserved", _("Reserved for landlord")
        PAID = "paid", _("Paid")
        CANCELED = "canceled", _("Canceled")

    lease = models.ForeignKey(
        Lease,
        related_name="extra_payments",
        on_delete=models.CASCADE,
        verbose_name=_("Lease"),
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    direction = models.CharField(_("Direction"), max_length=32, choices=Direction.choices)
    status = models.CharField(_("Status"), max_length=20, choices=Status.choices, default=Status.PLANNED)
    agreed_date = models.DateField(_("Agreed date"), help_text=_("Date when the parties agreed on this payment."))
    paid_date = models.DateField(
        _("Paid date"), null=True, blank=True, help_text=_("Actual date of payment (if paid).")
    )
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        ordering = ("-agreed_date", "id")
        verbose_name = _("Extra payment")
        verbose_name_plural = _("Extra payments")
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="extra_payment_amount_gt_0",
            ),
            models.CheckConstraint(
                check=(models.Q(paid_date__isnull=True) | models.Q(paid_date__gte=models.F("agreed_date"))),
                name="extra_payment_paid_after_agreed",
            ),
        ]

    def __str__(self) -> str:
        return _("%(title)s: %(amount)s (%(direction)s)") % {
            "title": self.title,
            "amount": self.amount,
            "direction": self.get_direction_display(),
        }


class MoneyTransaction(models.Model):
    lease = models.ForeignKey(
        Lease, related_name="money_transactions", on_delete=models.CASCADE, verbose_name=_("Lease")
    )
    date = models.DateField(_("Date"), help_text=_("Date when the money moved or is expected to move."))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    notes = models.CharField(_("Notes"), max_length=255, blank=True)
    payments_covered = models.ManyToManyField(
        Payment, related_name="money_transactions", verbose_name=_("Payments covered")
    )
    extra_payments_covered = models.ManyToManyField(
        ExtraPayment, related_name="money_transactions", verbose_name=_("Extra payments covered")
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    def __str__(self) -> str:
        return f"{self.date}: {self.amount}"
