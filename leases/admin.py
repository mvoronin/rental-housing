from django.contrib import admin

from .models import ExtraPayment, Lease, MoneyTransaction, Payment, RentRate


class RentRateInline(admin.TabularInline):
    model = RentRate
    extra = 0
    autocomplete_fields = []


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class ExtraPaymentInline(admin.TabularInline):
    model = ExtraPayment
    extra = 0


class MoneyTransactionInline(admin.TabularInline):
    model = MoneyTransaction
    extra = 0
    autocomplete_fields = ["payments_covered", "extra_payments_covered"]


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ("__str__", "first_period_start", "currency")
    list_filter = ("currency",)
    search_fields = ("title",)
    inlines = [RentRateInline, PaymentInline, ExtraPaymentInline, MoneyTransactionInline]


@admin.register(RentRate)
class RentRateAdmin(admin.ModelAdmin):
    list_display = ("lease", "amount", "effective_date", "end_date")
    list_filter = ("lease",)
    search_fields = ("lease__title", "notes")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("lease", "amount", "status", "date", "target_period_start")
    list_filter = ("status", "lease")
    search_fields = ("notes",)


@admin.register(ExtraPayment)
class ExtraPaymentAdmin(admin.ModelAdmin):
    list_display = ("lease", "title", "direction", "status", "amount", "agreed_date", "paid_date")
    list_filter = ("direction", "status", "lease")
    search_fields = ("title", "description")


@admin.register(MoneyTransaction)
class MoneyTransactionAdmin(admin.ModelAdmin):
    list_display = ("lease", "date", "amount", "created_at")
    list_filter = ("lease", "date")
    search_fields = ("notes",)
    filter_horizontal = ("payments_covered", "extra_payments_covered")
