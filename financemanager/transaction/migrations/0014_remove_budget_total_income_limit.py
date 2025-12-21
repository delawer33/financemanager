# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0013_account_recurringtransaction_account_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budget',
            name='total_income_limit',
        ),
    ]

