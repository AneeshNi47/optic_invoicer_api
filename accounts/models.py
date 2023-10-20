from django.db import models
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User

class Invitation(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    token = models.CharField(default=get_random_string, max_length=50, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_created')
    status = models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending', max_length=10)

    def send_invitation(self):
        subject = 'You are invited!'
        message = f'You have been invited. Click the link to register: {settings.FRONTEND_URL}{reverse("invitation_register", args=[self.token])}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.email]
        send_mail(subject, message, from_email, recipient_list)