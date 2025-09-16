from rest_framework import serializers
from .models import Transaction
import os

class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        max_size_mb = 25
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max {max_size_mb} MB")
        content_type = getattr(value, 'content_type', None)
        filename = getattr(value, 'name', '') or ''
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        allowed_pdf_types = {"application/pdf", "application/x-pdf"}
        allowed_csv_types = {"text/csv", "application/csv", "application/vnd.ms-excel"}

        is_pdf = (ext == ".pdf") and (content_type in allowed_pdf_types or content_type is None)
        is_csv = (ext == ".csv") and (content_type in allowed_csv_types or content_type is None)

        if not (is_pdf or is_csv):
            raise serializers.ValidationError("Only PDF or CSV files are allowed")
        return value

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["date", "narration", "debit", "credit", "balance"]
