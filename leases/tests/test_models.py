from datetime import date
from decimal import Decimal

from leases.models import ExtraPayment, Lease, Payment, RentRate


class TestLease:
    def test_create_lease(self, db):
        lease = Lease.objects.create(
            title="My Apartment",
            first_period_start=date(2024, 1, 1),
            currency=Lease.Currency.RUB,
        )
        assert lease.pk is not None
        assert str(lease) == "My Apartment"

    def test_lease_without_title(self, db):
        lease = Lease.objects.create(
            first_period_start=date(2024, 6, 15),
            currency=Lease.Currency.USD,
        )
        assert "2024-06-15" in str(lease)

    def test_lease_ordering(self, db):
        Lease.objects.create(first_period_start=date(2023, 1, 1))
        lease2 = Lease.objects.create(first_period_start=date(2024, 1, 1))
        leases = list(Lease.objects.all())
        assert leases[0] == lease2  # Newer first


class TestRentRate:
    def test_create_rent_rate(self, lease):
        rate = RentRate.objects.create(
            lease=lease,
            amount=Decimal("45000.00"),
            effective_date=date(2024, 1, 1),
        )
        assert rate.pk is not None
        assert "45000" in str(rate)

    def test_rent_rate_with_end_date(self, lease):
        rate = RentRate.objects.create(
            lease=lease,
            amount=Decimal("40000.00"),
            effective_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
        )
        assert "2024-06-30" in str(rate)


class TestPayment:
    def test_create_payment(self, lease):
        payment = Payment.objects.create(
            lease=lease,
            date=date(2024, 1, 15),
            amount=Decimal("50000.00"),
            status=Payment.Status.PAID,
        )
        assert payment.pk is not None

    def test_payment_statuses(self, lease):
        for status in Payment.Status:
            payment = Payment.objects.create(
                lease=lease,
                date=date(2024, 1, 1),
                amount=Decimal("1000.00"),
                status=status,
            )
            assert payment.status == status

    def test_payment_ordering(self, lease):
        Payment.objects.create(lease=lease, date=date(2024, 1, 1), amount=Decimal("100"))
        p2 = Payment.objects.create(lease=lease, date=date(2024, 2, 1), amount=Decimal("100"))
        payments = list(lease.payments.all())
        assert payments[0] == p2  # Newer first


class TestExtraPayment:
    def test_create_extra_payment(self, lease):
        extra = ExtraPayment.objects.create(
            lease=lease,
            title="Security Deposit",
            direction=ExtraPayment.Direction.TENANT_TO_LANDLORD,
            status=ExtraPayment.Status.PAID,
            agreed_date=date(2024, 1, 1),
            amount=Decimal("100000.00"),
        )
        assert extra.pk is not None
        assert "Security Deposit" in str(extra)

    def test_extra_payment_directions(self, lease):
        for direction in ExtraPayment.Direction:
            extra = ExtraPayment.objects.create(
                lease=lease,
                title="Test",
                direction=direction,
                agreed_date=date(2024, 1, 1),
                amount=Decimal("1000.00"),
            )
            assert extra.direction == direction
