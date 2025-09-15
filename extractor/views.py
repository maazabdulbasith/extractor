import os
import tempfile
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import GenericAPIView
from .serializers import PDFUploadSerializer, TransactionSerializer
from .pdf_extractor import extract_text_from_pdf
from .text_parser import parse_bank_statement
from .models import PDFUpload, Transaction

class PDFUploadView(GenericAPIView):
    serializer_class = PDFUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            pdf_file = serializer.validated_data['file']

            # Save temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_path = temp_file.name
            try:
                with open(temp_path, 'wb+') as dest:
                    for chunk in pdf_file.chunks():
                        dest.write(chunk)

                # Step 1: Extract text
                extracted_text = extract_text_from_pdf(temp_path)

                # Step 2: Parse into transactions (best-effort)
                try:
                    parsed = parse_bank_statement(extracted_text)
                except Exception:
                    parsed = []

                # Step 3: Save PDF upload record (uses file_name field)
                pdf_record = PDFUpload.objects.create(file_name=getattr(pdf_file, 'name', 'uploaded.pdf'))

                # Step 4: Save each transaction
                created_txns = []
                for txn in parsed:
                    created = Transaction.objects.create(
                        pdf=pdf_record,
                        date=txn['date'],
                        narration=txn['narration'],
                        debit=txn.get('debit') or None,
                        credit=txn.get('credit') or None,
                        balance=txn.get('balance') or None,
                    )
                    created_txns.append(created)

                # Step 5: Return both raw text and serialized transactions
                return Response({
                    "text": extracted_text,
                    "transactions": TransactionSerializer(created_txns, many=True).data,
                    "transaction_count": len(created_txns)
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                # Cleanup temp file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
