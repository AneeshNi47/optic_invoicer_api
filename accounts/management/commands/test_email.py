from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging
class Command(BaseCommand):
    help = 'Sends a test email to the email address specified in the command line.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email address to send the test email to.')

    def handle(self, *args, **kwargs):
        email = kwargs['email']
        subject = 'Test Email from Django'
        message = 'This is a test email sent from the Django application.'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        try:
            send_mail(subject, message, email_from, recipient_list, auth_password=settings.EMAIL_HOST_PASSWORD, auth_user=settings.EMAIL_HOST_USER)
            self.stdout.write(self.style.SUCCESS('Successfully sent test email to %s' % email))
        except Exception as e:
            logging.error('Error sending email: %s', e)
            self.stdout.write(self.style.ERROR('Failed to send test email: %s' % str(e)))


