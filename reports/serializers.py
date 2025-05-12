from rest_framework import serializers
from .models import (
    PaymentsCollectedReport,
    ActiveGroupsReport,
    AmountLoanedReport,
    ActiveLoansReport
)
from users.serializers import UserSerializer

class PaymentsCollectedReportSerializer(serializers.ModelSerializer):
    generated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PaymentsCollectedReport
        fields = '__all__'

class ActiveGroupsReportSerializer(serializers.ModelSerializer):
    generated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ActiveGroupsReport
        fields = '__all__'

class AmountLoanedReportSerializer(serializers.ModelSerializer):
    generated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AmountLoanedReport
        fields = '__all__'

class ActiveLoansReportSerializer(serializers.ModelSerializer):
    generated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ActiveLoansReport
        fields = '__all__'