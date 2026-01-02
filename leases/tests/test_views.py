from datetime import date
from decimal import Decimal

from django.urls import reverse

from leases.models import Lease, Payment, RentRate


class TestLeaseListView:
    def test_list_empty(self, client, db):
        response = client.get(reverse("leases:lease_list"))
        assert response.status_code == 200
        assert b"No leases found" in response.content

    def test_list_with_leases(self, client, lease):
        response = client.get(reverse("leases:lease_list"))
        assert response.status_code == 200
        assert lease.title.encode() in response.content

    def test_search(self, client, lease):
        response = client.get(reverse("leases:lease_list"), {"search": lease.title})
        assert response.status_code == 200
        assert lease.title.encode() in response.content


class TestLeaseDetailView:
    def test_detail(self, client, lease):
        response = client.get(reverse("leases:lease_detail", args=[lease.pk]))
        assert response.status_code == 200
        assert lease.title.encode() in response.content

    def test_detail_not_found(self, client, db):
        response = client.get(reverse("leases:lease_detail", args=[99999]))
        assert response.status_code == 404

    def test_detail_with_payments(self, client, lease, payment):
        response = client.get(reverse("leases:lease_detail", args=[lease.pk]))
        assert response.status_code == 200
        assert b"50000" in response.content


class TestLeaseCreateView:
    def test_get_form(self, client, db):
        response = client.get(reverse("leases:lease_create"))
        assert response.status_code == 200

    def test_create_lease(self, client, db):
        response = client.post(
            reverse("leases:lease_create"),
            {
                "title": "New Lease",
                "first_period_start": "2024-01-01",
                "currency": "RUB",
            },
        )
        assert response.status_code == 302
        assert Lease.objects.filter(title="New Lease").exists()


class TestLeaseUpdateView:
    def test_update_lease(self, client, lease):
        response = client.post(
            reverse("leases:lease_update", args=[lease.pk]),
            {
                "title": "Updated Title",
                "first_period_start": "2024-01-01",
                "currency": "RUB",
            },
        )
        assert response.status_code == 302
        lease.refresh_from_db()
        assert lease.title == "Updated Title"


class TestLeaseDeleteView:
    def test_delete_lease(self, client, lease):
        response = client.post(reverse("leases:lease_delete", args=[lease.pk]))
        assert response.status_code == 302
        assert not Lease.objects.filter(pk=lease.pk).exists()


class TestRentRateViews:
    def test_create_rent_rate(self, client, lease):
        response = client.post(
            reverse("leases:rent_rate_create", args=[lease.pk]),
            {
                "amount": "55000.00",
                "effective_date": "2024-02-01",
                "notes": "",
            },
        )
        assert response.status_code == 302
        assert RentRate.objects.filter(lease=lease, amount=Decimal("55000.00")).exists()

    def test_create_closes_previous_rate(self, client, lease, rent_rate):
        response = client.post(
            reverse("leases:rent_rate_create", args=[lease.pk]),
            {
                "amount": "60000.00",
                "effective_date": "2024-03-01",
                "notes": "",
            },
        )
        assert response.status_code == 302
        rent_rate.refresh_from_db()
        assert rent_rate.end_date == date(2024, 2, 29)  # Day before new rate


class TestPaymentViews:
    def test_create_payment(self, client, lease):
        response = client.post(
            reverse("leases:payment_create", args=[lease.pk]),
            {
                "date": "2024-01-15",
                "amount": "50000.00",
                "status": "paid",
                "target_period_start": "2024-01-01",
                "notes": "",
            },
        )
        assert response.status_code == 302
        assert Payment.objects.filter(lease=lease).exists()

    def test_quick_create_payment(self, client, lease, rent_rate):
        response = client.post(
            reverse("leases:payment_quick_create", args=[lease.pk]),
            {"status": "planned", "target_period_start": "2024-01-01"},
        )
        assert response.status_code == 200
        assert Payment.objects.filter(lease=lease).exists()

    def test_delete_payment(self, client, lease, payment):
        response = client.post(reverse("leases:payment_delete", args=[lease.pk, payment.pk]))
        assert response.status_code == 302
        assert not Payment.objects.filter(pk=payment.pk).exists()
