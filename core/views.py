from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from users.models import User
from .models import GroupLoanPayment, IndividualLoan, GroupLoan, GroupMemberStatus, IndividualLoanPayment
from .serializers import GroupLoanPaymentSerializer, IndividualLoanPaymentSerializer, IndividualLoanSerializer, GroupLoanSerializer, GroupMemberStatusSerializer
from .permissions import IsLoanOfficerOrHigher
from core import serializers

from core import models

class IndividualLoanViewSet(viewsets.ModelViewSet):
    queryset = IndividualLoan.objects.all().order_by('-created_at')
    serializer_class = IndividualLoanSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]

    def perform_create(self, serializer):
        serializer.save(loan_officer=self.request.user)

    def get_queryset(self):
        user = self.request.user
        # print(f"Debug - User role: {user.role}")  # Check what role is being detected
        
        if user.role in ['superuser', 'manager', 'region_manager']:
            return IndividualLoan.objects.all().order_by('-created_at')
        elif user.role == 'loan_officer':
            return IndividualLoan.objects.filter(loan_officer=user).order_by('-created_at')
        else:
            # For regular users, show loans where they're either officer OR recipient
            return IndividualLoan.objects.filter(
                models.Q(loan_officer=user) | 
                models.Q(recipient=user)
                .order_by('-created_at')
            )

                
class GroupLoanViewSet(viewsets.ModelViewSet):
    queryset = GroupLoan.objects.all().order_by('-created_at')
    serializer_class = GroupLoanSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]

    def perform_create(self, serializer):
        try:
            serializer.save(loan_officer=self.request.user)
        except ValidationError as e:
            raise serializers.ValidationError({'detail': str(e)})

    def get_queryset(self):
        user = self.request.user
        if user.role in ['superuser', 'manager', 'region_manager']:
            return self.queryset
        elif user.role == 'loan_officer':
            return self.queryset.filter(loan_officer=user)
        else:
            return self.queryset.filter(members=user)

class GroupMemberStatusViewSet(viewsets.ModelViewSet):
    serializer_class = GroupMemberStatusSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]
    queryset = GroupMemberStatus.objects.all().order_by('-blocked_at')
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if group_loan_id := self.request.query_params.get('group_loan'):
            queryset = queryset.filter(group_loan_id=group_loan_id)
        
        if frequency_letter := self.request.query_params.get('frequency_letter'):
            queryset = queryset.filter(frequency_letter=frequency_letter)
        
        if user.role in ['superuser', 'manager', 'region_manager']:
            return queryset
        elif user.role == 'loan_officer':
            return queryset.filter(group_loan__loan_officer=user)
        return queryset.filter(member=user)
    
    def perform_update(self, serializer):
        if 'is_blocked' in serializer.validated_data:
            if serializer.validated_data['is_blocked']:
                serializer.validated_data['blocked_by'] = self.request.user
                serializer.validated_data['blocked_at'] = timezone.now()
            else:
                serializer.validated_data['blocked_by'] = None
                serializer.validated_data['blocked_at'] = None
        serializer.save()

class IndividualLoanPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualLoanPaymentSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]
    
    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        return IndividualLoanPayment.objects.filter(loan_id=loan_id).order_by('-payment_date')
    
    def perform_create(self, serializer):
        loan = get_object_or_404(IndividualLoan, pk=self.kwargs.get('loan_id'))
        amount = serializer.validated_data['amount']
        payment = loan.make_payment(amount, self.request.user)
        serializer.instance = payment

    # @action(detail=True, methods=['get'], url_path='payments')
    # def list_payments(self, request, pk=None):
    #     loan = self.get_object()
    #     payments = loan.payments.all().order_by('-payment_date')
    #     serializer = IndividualLoanPaymentSerializer(payments, many=True)
    #     return Response(serializer.data)

class GroupLoanPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = GroupLoanPaymentSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]
    
    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        return GroupLoanPayment.objects.filter(loan_id=loan_id).order_by('-payment_date')
    
    def perform_create(self, serializer):
        loan = get_object_or_404(GroupLoan, pk=self.kwargs.get('loan_id'))
        member = get_object_or_404(User, pk=serializer.validated_data['member_id'])
        amount = serializer.validated_data['amount']
        payment = loan.make_payment(amount, self.request.user, member)
        serializer.instance = payment

    # @action(detail=True, methods=['get'], url_path='payments')
    # def list_payments(self, request, pk=None):
    #     loan = self.get_object()
    #     payments = loan.payments.all().order_by('-payment_date')
    #     serializer = GroupLoanPaymentSerializer(payments, many=True)
    #     return Response(serializer.data)

class IndividualLoanPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualLoanPaymentSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]
    
    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        return IndividualLoanPayment.objects.filter(loan_id=loan_id).order_by('-payment_date')
    
    def perform_create(self, serializer):
        loan = get_object_or_404(IndividualLoan, pk=self.kwargs.get('loan_id'))
        amount = serializer.validated_data['amount']
        payment = loan.make_payment(amount, self.request.user)
        serializer.instance = payment

    

class GroupLoanPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = GroupLoanPaymentSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]
    
    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        return GroupLoanPayment.objects.filter(loan_id=loan_id).order_by('-payment_date')
    
    def perform_create(self, serializer):
        loan = get_object_or_404(GroupLoan, pk=self.kwargs.get('loan_id'))
        member = get_object_or_404(User, pk=serializer.validated_data['member_id'])
        amount = serializer.validated_data['amount']
        payment = loan.make_payment(amount, self.request.user, member)
        serializer.instance = payment