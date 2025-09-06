from django.db import models

class User(models.Model):
    email=models.EmailField(unique=True)
    password=models.CharField(max_length=100)
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table='users'

    @property
    def is_authenticated(self):
        return True

