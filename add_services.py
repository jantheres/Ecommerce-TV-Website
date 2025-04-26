import os
import django
import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from eapp.models import Service

# Create default services
services = [
    {
        'name': 'TV Installation Service',
        'service_type': 'installation',
        'description': 'Professional TV mounting and installation service. Includes wall mounting, cable management, and basic setup of TV channels and connected devices.',
        'price': 1499.00,
        'duration': datetime.timedelta(hours=2),
        'is_available': True
    },
    {
        'name': 'TV Repair Service',
        'service_type': 'repair',
        'description': 'Expert TV repair service for all major brands. Includes diagnosis, repair of common issues like display problems, sound issues, and power problems.',
        'price': 999.00,
        'duration': datetime.timedelta(hours=3),
        'is_available': True
    },
    {
        'name': 'TV Maintenance Service',
        'service_type': 'maintenance',
        'description': 'Comprehensive TV maintenance service including cleaning, software updates, picture quality optimization, and preventive checks.',
        'price': 699.00,
        'duration': datetime.timedelta(hours=1, minutes=30),
        'is_available': True
    }
]

# Add services to database
for service_data in services:
    Service.objects.get_or_create(
        name=service_data['name'],
        defaults=service_data
    )

print("Services added successfully!")
