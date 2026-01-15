import csv
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError
from io import TextIOWrapper
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer
from .models import Transaction
from .serializer import TransactionSerializer

# Create your views here.

class CSVUploadAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)  # This allows handling file uploads

    def post(self, request):
        # Check if the request contains a CSV file
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                # Read CSV file
                # csvfile = TextIOWrapper(file, encoding='utf-8')
                csvfile = file.read().decode('utf-8').splitlines()
                csv_reader = csv.DictReader(csvfile)
                next(csv_reader)


                # Parse and create transactions from CSV
                for row in csv_reader:
                    transaction_data = {
                        'transaction_id': row.get('transaction_id'),
                        'credit_amt': row.get('credit_amt'),
                        'debit_amt': row.get('debit_amt'),
                        'description': row.get('description'),
                        'deposite_type': row.get('deposite_type'),
                        'expense_type': row.get('expense_type'),
                        'customer_id': row.get('customer_id'),
                    }
                    print(row)

                    # Check if the customer_id exists in the Customer model
                    customer = Customer.objects.filter(id=row.get('customer_id')).first()
                    if not customer:
                        raise ValidationError(f"Customer with ID {row.get('customer_id')} not found.")

                    serializer = TransactionSerializer(data=transaction_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        raise ValidationError(f"Invalid data in row {csv_reader.line_num}: {serializer.errors}")
                
                return Response({"message": "Transactions added successfully!"}, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
    
class TransactionAPI(APIView):
    
    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        if id:
            try:
                transaction = Transaction.objects.get(id=id)  # Corrected to .objects
            except Transaction.DoesNotExist:
                return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = TransactionSerializer(transaction)
            return Response(serializer.data)

        transactions = Transaction.objects.all()  # Corrected to .objects
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def put(self, request, id):
        if id:
            try:
                transaction = Transaction.objects.get(id=id)  # Corrected to .objects
            except Transaction.DoesNotExist:  # Corrected exception type
                return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = TransactionSerializer(transaction, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)
        except Transaction.DoesNotExist:
            return Response({'error': "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        transaction.delete()
        return Response({"message": "Customer Deleted"}, status=status.HTTP_204_NO_CONTENT)
