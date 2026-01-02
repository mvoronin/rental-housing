import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def lease(db):
    from datetime import date

    from leases.models import Lease

    return Lease.objects.create(
        title="Test Lease",
        first_period_start=date(2024, 1, 1),
        currency=Lease.Currency.RUB,
    )


@pytest.fixture
def rent_rate(db, lease):
    from datetime import date
    from decimal import Decimal

    from leases.models import RentRate

    return RentRate.objects.create(
        lease=lease,
        amount=Decimal("50000.00"),
        effective_date=date(2024, 1, 1),
    )


@pytest.fixture
def payment(db, lease):
    from datetime import date
    from decimal import Decimal

    from leases.models import Payment

    return Payment.objects.create(
        lease=lease,
        date=date(2024, 1, 15),
        amount=Decimal("50000.00"),
        status=Payment.Status.PAID,
        target_period_start=date(2024, 1, 1),
    )
