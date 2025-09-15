from django.db import models

class PDFUpload(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class Transaction(models.Model):
    pdf = models.ForeignKey(PDFUpload, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateField()
    narration = models.TextField()
    debit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    credit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.date} - {self.narration[:30]}"
