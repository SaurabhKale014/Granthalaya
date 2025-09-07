from django.db import models
from accounts.models import User  # Your custom User model
from library.models import Book   # Your Book model

class BorrowRecord(models.Model):
    STATUS_CHOICES=[
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('return_requested', 'Return Requested'),
        ('return_verified', 'Return Verified'),
        ('damage_reported', 'Damage Reported'),
    ]
    user=models.ForeignKey(User, on_delete=models.CASCADE,  related_name='borrow_records')
    book=models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    status=models.CharField(max_length=20, choices=STATUS_CHOICES,default='pending-approval')
    borrow_requested_at = models.DateTimeField(auto_now_add=True)
    borrow_approved_at = models.DateTimeField(null=True, blank=True)
    return_requested_at = models.DateTimeField(null=True, blank=True)
    return_verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True,null=True)

    class Meta:
        db_table='borrow_records'
