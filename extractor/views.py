import os
import tempfile
import logging
from decimal import Decimal
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import GenericAPIView
from .serializers import PDFUploadSerializer, TransactionSerializer
from .pdf_extractor import extract_text_from_pdf
from .text_parser import parse_bank_statement
from .models import PDFUpload, Transaction
from .csv_extractor import extract_text_from_csv

logger = logging.getLogger(__name__)

class PDFUploadView(GenericAPIView):
    serializer_class = PDFUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = serializer.validated_data['file']

        filename = getattr(pdf_file, 'name', '') or ''
        content_type = getattr(pdf_file, 'content_type', None)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        allowed_csv_types = {"text/csv", "application/csv", "application/vnd.ms-excel"}
        is_csv = (ext == '.csv') or (content_type in allowed_csv_types)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv' if is_csv else '.pdf')
        temp_path = temp_file.name
        try:
            with open(temp_path, 'wb+') as dest:
                for chunk in pdf_file.chunks():
                    dest.write(chunk)

            if is_csv:
                try:
                    with open(temp_path, 'rb') as f:
                        parsed = extract_text_from_csv(f)
                except Exception:
                    parsed = []
                extracted_text = "CSV Upload"
            else:
                extracted_text = extract_text_from_pdf(temp_path)
                try:
                    parsed = parse_bank_statement(extracted_text)
                except Exception:
                    parsed = []

            with transaction.atomic():
                pdf_record = PDFUpload.objects.create(file_name=getattr(pdf_file, 'name', 'uploaded.pdf'))

                transactions_to_create = []
                for txn in parsed:
                    debit = txn.get('debit')
                    credit = txn.get('credit')
                    balance = txn.get('balance')
                    transactions_to_create.append(
                        Transaction(
                            pdf=pdf_record,
                            date=txn['date'],
                            narration=txn['narration'],
                            debit=Decimal(str(debit)) if debit not in (None, 0, 0.0, "") else None,
                            credit=Decimal(str(credit)) if credit not in (None, 0, 0.0, "") else None,
                            balance=Decimal(str(balance)) if balance not in (None, 0, 0.0, "") else None,
                        )
                    )
                if transactions_to_create:
                    Transaction.objects.bulk_create(transactions_to_create)

            saved_txns = Transaction.objects.filter(pdf=pdf_record).order_by('id')

            return Response({
                "text": extracted_text,
                "transactions": TransactionSerializer(saved_txns, many=True).data,
                "transaction_count": saved_txns.count(),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Failed processing PDF upload")
            message = str(e)
            error_type = e.__class__.__name__
            hint = None
            lower = message.lower()
            if "poppler" in lower:
                hint = "Install Poppler and set POPPLER_PATH or add poppler bin to PATH."
            elif "tesseract" in lower:
                hint = "Install Tesseract OCR and add to PATH, or set pytesseract.pytesseract.tesseract_cmd."
            elif "could not connect to server" in lower or "connection refused" in lower:
                hint = "Ensure PostgreSQL is running and credentials in settings.py are correct."
            return Response({
                "error": message,
                "error_type": error_type,
                **({"hint": hint} if hint else {})
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
