# Generated by Django 5.1.6 on 2025-02-05 21:20

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('type', models.CharField(choices=[('INCOME', 'Income'), ('OUTCOME', 'Outcome')], default='OUTCOME', max_length=20, verbose_name='Type')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('INCOME', 'Income'), ('OUTCOME', 'Outcome')], default='OUTCOME', max_length=20, verbose_name='Type')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=16)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('description', models.TextField(blank=True, max_length=255, null=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='transaction.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
