from decimal import Decimal

from django.db import migrations

PLAN_PRICES = {
    "starter": Decimal("2000.00"),
    "pro": Decimal("5000.00"),
    "premium": Decimal("10000.00"),
}


def update_plan_prices(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "SubscriptionPlan")
    for slug, amount in PLAN_PRICES.items():
        Plan.objects.filter(slug=slug).update(monthly_amount=amount)


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0003_alter_subscriptionpayment_provider"),
    ]

    operations = [
        migrations.RunPython(update_plan_prices, migrations.RunPython.noop),
    ]
