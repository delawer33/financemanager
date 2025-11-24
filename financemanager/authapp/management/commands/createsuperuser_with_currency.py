from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authapp.models import Currency


class Command(BaseCommand):
    help = 'Create a superuser with default currency'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address')
        parser.add_argument('--password', type=str, help='Password')
        parser.add_argument('--firstname', type=str, help='First name', default='')
        parser.add_argument('--lastname', type=str, help='Last name', default='')
        parser.add_argument('--currency', type=str, help='Currency symbol (default: USD)', default='USD')

    def handle(self, *args, **options):
        User = get_user_model()
        
        try:
            currency = Currency.objects.get(symbol=options['currency'])
        except Currency.DoesNotExist:
            currency = Currency.objects.first()
            if not currency:
                self.stdout.write(
                    self.style.ERROR('No currencies found. Please run: python manage.py init_currencies')
                )
                return
        
        email = options['email'] or input('Email: ')
        password = options['password'] or input('Password: ')
        firstname = options['firstname'] or input('First name (optional): ')
        lastname = options['lastname'] or input('Last name (optional): ')
        
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                firstname=firstname,
                lastname=lastname,
                currency=currency
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser created successfully: {user.email}')
            )
            self.stdout.write(f'Default currency: {currency.name} ({currency.symbol})')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
