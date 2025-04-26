from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from eapp.models import Technician

class Command(BaseCommand):
    help = 'Creates a technician user account'

    def handle(self, *args, **kwargs):
        # Create a user for the technician
        email = 'technician@primepixels.com'
        password = 'Tech@123'
        username = 'technician1'

        # Delete existing user if it exists
        User.objects.filter(email=email).delete()

        # Create new user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.first_name = 'John'
        user.last_name = 'Smith'
        user.save()

        # Create technician profile
        technician = Technician.objects.create(
            user=user,
            name='John Smith',
            phone_number='1234567890',
            expertise='TV Repair and Installation'
        )

        self.stdout.write(self.style.SUCCESS(f'''
Technician account created successfully!

Login Credentials:
Email: {email}
Password: {password}

Please use these credentials at http://127.0.0.1:8000/technician/login/
'''))
