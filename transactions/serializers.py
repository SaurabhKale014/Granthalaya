from .models import BorrowRecord
from rest_framework import serializers

class BorrowRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model=BorrowRecord
        fields='__all__'
        ready_only_fields=('borrow_requested_at', 'borrow_approved_at', 'return_requested_at', 'return_verified_at')