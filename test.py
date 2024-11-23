from django.core.mail import send_mail

send_mail(
    'Test Email Subject',
    'This is a test email message.',
    'admin@localhost',  # From email
    ['recipient@example.com'],  # To email
    fail_silently=False,
)