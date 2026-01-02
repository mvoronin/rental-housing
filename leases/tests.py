from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .api import (
    lease_add_rent_rate,
    lease_get,
    lease_get_list,
    lease_money_transaction_create,
    lease_payment_update,
    lease_payments,
)
from .models import ExtraPayment, Lease, MoneyTransaction, Payment, RentRate


class LeaseApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def _json(self, response):
        return json.loads(response.content.decode("utf-8"))

    def test_lease_get_list_orders_results(self) -> None:
        lease_old = Lease.objects.create(title="Old Flat", first_period_start=date(2023, 1, 1))
        lease_new = Lease.objects.create(title="New Flat", first_period_start=date(2024, 5, 1))
        lease_mid = Lease.objects.create(title="Mid Flat", first_period_start=date(2024, 1, 1))

        request = self.factory.get("/api/leases/")
        response = lease_get_list(request)
        data = self._json(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["results"]), 3)
        self.assertEqual(
            [item["id"] for item in data["results"]],
            [lease_new.id, lease_mid.id, lease_old.id],
        )

        self.assertEqual(data["results"][0]["currency_symbol"], "₽")

    def test_lease_get_list_filters_by_search_and_dates(self) -> None:
        lease_a = Lease.objects.create(title="Penthouse", first_period_start=date(2024, 2, 1))
        lease_b = Lease.objects.create(title="Garden Apartment", first_period_start=date(2024, 4, 1))
        Lease.objects.create(title="Basement", first_period_start=date(2023, 12, 1))

        request_search = self.factory.get("/api/leases/", {"search": "Pent"})
        response_search = lease_get_list(request_search)
        data_search = self._json(response_search)
        self.assertEqual(len(data_search["results"]), 1)
        self.assertEqual(data_search["results"][0]["id"], lease_a.id)

        request_id_search = self.factory.get("/api/leases/", {"search": str(lease_b.id)})
        data_id_search = self._json(lease_get_list(request_id_search))
        self.assertEqual(len(data_id_search["results"]), 1)
        self.assertEqual(data_id_search["results"][0]["id"], lease_b.id)

        request_filter = self.factory.get(
            "/api/leases/",
            {
                "first_period_start_before": "2024-03-01",
                "first_period_start_after": "2023-12-15",
            },
        )
        data_filter = self._json(lease_get_list(request_filter))
        self.assertEqual(len(data_filter["results"]), 1)
        self.assertEqual(data_filter["results"][0]["id"], lease_a.id)

    def test_lease_post_creates_instance(self) -> None:
        payload = {
            "title": "New Lease",
            "first_period_start": "2024-06-01",
            "currency": "usd",
            "notes": "Furnished",
        }
        request = self.factory.post(
            "/api/leases/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_get_list(request)
        data = self._json(response)

        lease = Lease.objects.get(pk=data["id"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], reverse("leases:lease-detail", args=[lease.id]))
        self.assertEqual(data["currency"], "USD")
        self.assertEqual(data["notes"], "Furnished")
        self.assertEqual(data["first_period_start"], "2024-06-01")
        self.assertEqual(lease.currency, "USD")
        self.assertFalse(hasattr(lease, "notes"))

    def test_lease_post_validates_input(self) -> None:
        # Missing date
        request_missing = self.factory.post(
            "/api/leases/",
            data=json.dumps({"title": "Incomplete"}),
            content_type="application/json",
        )
        response_missing = lease_get_list(request_missing)
        self.assertEqual(response_missing.status_code, 400)

        # Invalid JSON
        request_invalid_json = self.factory.post(
            "/api/leases/",
            data="{broken}",
            content_type="application/json",
        )
        response_invalid_json = lease_get_list(request_invalid_json)
        self.assertEqual(response_invalid_json.status_code, 400)

        # Unsupported currency
        payload = {
            "title": "Lease",
            "first_period_start": "2024-01-01",
            "currency": "GBP",
        }
        request_bad_currency = self.factory.post(
            "/api/leases/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        response_bad_currency = lease_get_list(request_bad_currency)
        self.assertEqual(response_bad_currency.status_code, 400)
        self.assertEqual(Lease.objects.count(), 0)

    def test_lease_get_returns_related_data(self) -> None:
        lease = Lease.objects.create(title="Detail Lease", first_period_start=date(2024, 1, 1))
        RentRate.objects.create(
            lease=lease,
            amount=Decimal("1200.00"),
            effective_date=date(2024, 1, 1),
        )
        payment = Payment.objects.create(
            lease=lease,
            date=date(2024, 1, 15),
            amount=Decimal("1200.00"),
            status=Payment.Status.PAID,
            target_period_start=date(2024, 1, 1),
            notes="January rent",
        )
        extra = ExtraPayment.objects.create(
            lease=lease,
            title="Repair reimbursement",
            description="Window fix",
            direction=ExtraPayment.Direction.LANDLORD_TO_TENANT,
            status=ExtraPayment.Status.PAID,
            agreed_date=date(2024, 1, 20),
            paid_date=date(2024, 1, 25),
            amount=Decimal("150.00"),
        )

        request = self.factory.get(f"/api/leases/{lease.id}/")
        response = lease_get(request, lease_id=lease.id)
        data = self._json(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["id"], lease.id)
        self.assertEqual(data["currency_symbol"], "₽")
        self.assertEqual(len(data["rent_rates"]), 1)
        self.assertEqual(data["rent_rates"][0]["amount"], "1200.00")
        self.assertEqual(len(data["payments"]), 1)
        self.assertEqual(data["payments"][0]["status_label"], payment.get_status_display())
        self.assertNotIn("allocations", data["payments"][0])
        self.assertEqual(len(data["extra_payments"]), 1)
        self.assertEqual(data["extra_payments"][0]["direction_label"], extra.get_direction_display())

    def test_lease_delete_removes_record(self) -> None:
        lease = Lease.objects.create(title="To Delete", first_period_start=date(2024, 1, 1))

        request = self.factory.delete(f"/api/leases/{lease.id}/")
        response = lease_get(request, lease_id=lease.id)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Location"], reverse("leases:lease-list"))
        self.assertFalse(Lease.objects.filter(pk=lease.pk).exists())

    def test_lease_delete_missing_returns_404(self) -> None:
        request = self.factory.delete("/api/leases/999/")
        with self.assertRaises(Http404):
            lease_get(request, lease_id=999)

    def test_add_rent_rate_creates_record(self) -> None:
        lease = Lease.objects.create(title="Rated", first_period_start=date(2024, 1, 1))
        payload = {
            "amount": "950.50",
            "effective_date": "2024-01-01",
            "end_date": "2024-06-01",
            "notes": "Intro rate",
        }
        request = self.factory.post(
            f"/api/leases/{lease.id}/rent-rates/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_add_rent_rate(request, lease_id=lease.id)
        data = self._json(response)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], reverse("leases:lease-detail", args=[lease.id]))
        self.assertEqual(data["amount"], "950.50")
        self.assertEqual(data["effective_date"], "2024-01-01")
        self.assertEqual(data["end_date"], "2024-06-01")
        rate = RentRate.objects.get(lease=lease)
        self.assertEqual(rate.amount, Decimal("950.50"))
        self.assertEqual(rate.notes, "Intro rate")

    def test_add_rent_rate_validates_payload(self) -> None:
        lease = Lease.objects.create(title="Bad Rate", first_period_start=date(2024, 2, 1))

        # Missing amount
        request_missing = self.factory.post(
            f"/api/leases/{lease.id}/rent-rates/",
            data=json.dumps({"effective_date": "2024-02-01"}),
            content_type="application/json",
        )
        response_missing = lease_add_rent_rate(request_missing, lease_id=lease.id)
        self.assertEqual(response_missing.status_code, 400)

        # end_date before effective_date
        payload_invalid_dates = {
            "amount": "1000",
            "effective_date": "2024-03-01",
            "end_date": "2024-02-01",
        }
        request_invalid_dates = self.factory.post(
            f"/api/leases/{lease.id}/rent-rates/",
            data=json.dumps(payload_invalid_dates),
            content_type="application/json",
        )
        response_invalid_dates = lease_add_rent_rate(request_invalid_dates, lease_id=lease.id)
        self.assertEqual(response_invalid_dates.status_code, 400)
        self.assertEqual(RentRate.objects.filter(lease=lease).count(), 0)

    def test_create_payment_defaults_to_planned(self) -> None:
        lease = Lease.objects.create(title="Future payment", first_period_start=date(2024, 1, 1))
        request = self.factory.post(
            f"/api/leases/{lease.id}/payments/",
            data=json.dumps({"amount": "100.00", "date": "2024-01-01"}),
            content_type="application/json",
        )
        response = lease_payments(request, lease_id=lease.id)
        data = self._json(response)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], reverse("leases:lease-payments", args=[lease.id]))
        payment = Payment.objects.get(lease=lease)
        self.assertEqual(payment.status, Payment.Status.PLANNED)
        self.assertEqual(data["status"], Payment.Status.PLANNED)

    def test_create_payment_rejects_paid_status(self) -> None:
        lease = Lease.objects.create(title="Invalid status", first_period_start=date(2024, 1, 1))
        request = self.factory.post(
            f"/api/leases/{lease.id}/payments/",
            data=json.dumps({"amount": "100.00", "date": "2024-01-01", "status": "paid"}),
            content_type="application/json",
        )
        response = lease_payments(request, lease_id=lease.id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Payment.objects.filter(lease=lease).count(), 0)

    def test_create_payment_accepts_reserved_status(self) -> None:
        lease = Lease.objects.create(title="Reserved status", first_period_start=date(2024, 1, 1))
        request = self.factory.post(
            f"/api/leases/{lease.id}/payments/",
            data=json.dumps({"amount": "250.00", "date": "2024-02-01", "status": "reserved"}),
            content_type="application/json",
        )
        response = lease_payments(request, lease_id=lease.id)
        data = self._json(response)

        self.assertEqual(response.status_code, 201)
        payment = Payment.objects.get(lease=lease)
        self.assertEqual(payment.status, Payment.Status.RESERVED)
        self.assertEqual(data["status_label"], payment.get_status_display())

    def test_patch_payment_moves_planned_to_reserved(self) -> None:
        lease = Lease.objects.create(title="Patch payment", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            amount=Decimal("500.00"),
            date=date(2024, 2, 1),
            status=Payment.Status.PLANNED,
        )
        request = self.factory.patch(
            f"/api/leases/{lease.id}/payments/{payment.id}/",
            data=json.dumps({"status": "reserved"}),
            content_type="application/json",
        )
        response = lease_payment_update(request, lease_id=lease.id, payment_id=payment.id)
        data = self._json(response)

        payment.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.Status.RESERVED)
        self.assertEqual(data["status"], Payment.Status.RESERVED)

    def test_patch_payment_requires_planned_status(self) -> None:
        lease = Lease.objects.create(title="Patch invalid", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            amount=Decimal("500.00"),
            date=date(2024, 2, 1),
            status=Payment.Status.RESERVED,
        )
        request = self.factory.patch(
            f"/api/leases/{lease.id}/payments/{payment.id}/",
            data=json.dumps({"status": "reserved"}),
            content_type="application/json",
        )
        response = lease_payment_update(request, lease_id=lease.id, payment_id=payment.id)
        self.assertEqual(response.status_code, 400)

    def test_patch_payment_rejects_invalid_target_status(self) -> None:
        lease = Lease.objects.create(title="Patch invalid value", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            amount=Decimal("500.00"),
            date=date(2024, 2, 1),
            status=Payment.Status.PLANNED,
        )
        request = self.factory.patch(
            f"/api/leases/{lease.id}/payments/{payment.id}/",
            data=json.dumps({"status": "paid"}),
            content_type="application/json",
        )
        response = lease_payment_update(request, lease_id=lease.id, payment_id=payment.id)
        payment.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payment.status, Payment.Status.PLANNED)

    def test_delete_payment_removes_planned_payment(self) -> None:
        lease = Lease.objects.create(title="Delete planned", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            amount=Decimal("800.00"),
            date=date(2024, 2, 1),
            status=Payment.Status.PLANNED,
        )
        request = self.factory.delete(f"/api/leases/{lease.id}/payments/{payment.id}/")
        response = lease_payment_update(request, lease_id=lease.id, payment_id=payment.id)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Location"], reverse("leases:lease-payments", args=[lease.id]))
        self.assertFalse(Payment.objects.filter(pk=payment.id).exists())

    def test_delete_payment_disallows_non_planned(self) -> None:
        lease = Lease.objects.create(title="Delete reserved", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            amount=Decimal("900.00"),
            date=date(2024, 2, 1),
            status=Payment.Status.RESERVED,
        )
        request = self.factory.delete(f"/api/leases/{lease.id}/payments/{payment.id}/")
        response = lease_payment_update(request, lease_id=lease.id, payment_id=payment.id)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Payment.objects.filter(pk=payment.id).exists())

    def test_get_payments_returns_results_and_filters(self) -> None:
        lease = Lease.objects.create(title="With payments", first_period_start=date(2024, 1, 1))
        RentRate.objects.create(
            lease=lease,
            amount=Decimal("1100.00"),
            effective_date=date(2024, 1, 1),
        )
        Payment.objects.create(
            lease=lease,
            date=date(2024, 1, 10),
            amount=Decimal("1100.00"),
            status=Payment.Status.PAID,
        )
        Payment.objects.create(
            lease=lease,
            date=date(2024, 2, 10),
            amount=Decimal("1100.00"),
            status=Payment.Status.RESERVED,
        )

        request_all = self.factory.get(f"/api/leases/{lease.id}/payments/")
        response_all = lease_payments(request_all, lease_id=lease.id)
        data_all = self._json(response_all)
        self.assertEqual(response_all.status_code, 200)
        self.assertEqual(len(data_all["results"]), 2)
        self.assertNotIn("allocations", data_all["results"][1])

        request_filtered = self.factory.get(
            f"/api/leases/{lease.id}/payments/",
            {"status": "reserved"},
        )
        response_filtered = lease_payments(request_filtered, lease_id=lease.id)
        data_filtered = self._json(response_filtered)
        self.assertEqual(response_filtered.status_code, 200)
        self.assertEqual(len(data_filtered["results"]), 1)
        self.assertEqual(data_filtered["results"][0]["status"], Payment.Status.RESERVED)

    def test_create_money_transaction_marks_items_as_paid(self) -> None:
        lease = Lease.objects.create(title="Transactions", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            date=date(2024, 3, 1),
            amount=Decimal("700.00"),
            status=Payment.Status.PLANNED,
        )
        extra = ExtraPayment.objects.create(
            lease=lease,
            title="Cleaning",
            description="",
            direction=ExtraPayment.Direction.TENANT_TO_LANDLORD,
            status=ExtraPayment.Status.RESERVED,
            agreed_date=date(2024, 3, 1),
            amount=Decimal("300.00"),
        )

        payload = {
            "amount": "1000.00",
            "date": "2024-03-05",
            "payment_ids": [payment.id],
            "extra_payment_ids": [extra.id],
            "notes": "March settlement",
        }
        request = self.factory.post(
            f"/api/leases/{lease.id}/transactions/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_money_transaction_create(request, lease_id=lease.id)
        data = self._json(response)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Location"], reverse("leases:lease-transactions", args=[lease.id]))
        payment.refresh_from_db()
        extra.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(extra.status, ExtraPayment.Status.PAID)
        transaction = MoneyTransaction.objects.get(lease=lease)
        self.assertEqual(transaction.amount, Decimal("1000.00"))
        self.assertEqual(data["payment_ids"], [payment.id])
        self.assertEqual(data["extra_payment_ids"], [extra.id])

    def test_create_money_transaction_validates_amount(self) -> None:
        lease = Lease.objects.create(title="Transactions mismatch", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            date=date(2024, 3, 1),
            amount=Decimal("700.00"),
            status=Payment.Status.PLANNED,
        )

        payload = {
            "amount": "800.00",
            "date": "2024-03-05",
            "payment_ids": [payment.id],
            "extra_payment_ids": [],
        }
        request = self.factory.post(
            f"/api/leases/{lease.id}/transactions/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_money_transaction_create(request, lease_id=lease.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(MoneyTransaction.objects.count(), 0)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PLANNED)

    def test_create_money_transaction_checks_lease_ownership(self) -> None:
        lease = Lease.objects.create(title="Lease A", first_period_start=date(2024, 1, 1))
        other = Lease.objects.create(title="Lease B", first_period_start=date(2024, 2, 1))
        payment = Payment.objects.create(
            lease=other,
            date=date(2024, 3, 1),
            amount=Decimal("700.00"),
            status=Payment.Status.PLANNED,
        )

        payload = {
            "amount": "700.00",
            "date": "2024-03-05",
            "payment_ids": [payment.id],
        }
        request = self.factory.post(
            f"/api/leases/{lease.id}/transactions/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_money_transaction_create(request, lease_id=lease.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(MoneyTransaction.objects.count(), 0)

    def test_create_money_transaction_rejects_paid_payment(self) -> None:
        lease = Lease.objects.create(title="Lease statuses", first_period_start=date(2024, 1, 1))
        payment = Payment.objects.create(
            lease=lease,
            date=date(2024, 3, 1),
            amount=Decimal("700.00"),
            status=Payment.Status.PAID,
        )

        payload = {
            "amount": "700.00",
            "date": "2024-03-05",
            "payment_ids": [payment.id],
        }
        request = self.factory.post(
            f"/api/leases/{lease.id}/transactions/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        response = lease_money_transaction_create(request, lease_id=lease.id)
        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
