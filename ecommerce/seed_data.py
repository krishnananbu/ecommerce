import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from shop.models import Category, Product, Brand, ProductImage
from populate_store import run_seed

if __name__ == "__main__":
    run_seed()
