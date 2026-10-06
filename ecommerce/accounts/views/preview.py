from django.shortcuts import render
from django.conf import settings

def preview_welcome_email(request):
    context = {
        'user': {
            'first_name': 'Test User',
            'email': 'test@example.com'
        },
        'site_url': settings.SITE_URL
    }
    return render(request, 'shop/email/welcome.html', context)