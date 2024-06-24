from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.db import connection


@receiver(user_logged_out)
def close_db_connections(sender, request, user, **kwargs):
    connection.close()
