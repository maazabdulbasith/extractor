from rest_framework import serializers
from .models import Transaction

class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        max_size_mb = 25
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max {max_size_mb} MB")
        content_type = getattr(value, 'content_type', None)
        if content_type not in {"application/pdf", "application/x-pdf"}:
            raise serializers.ValidationError("Only PDF files are allowed")
        return value

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["date", "narration", "debit", "credit", "balance"]
