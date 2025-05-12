from django.forms import ValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import IndividualLoan, GroupLoan, GroupMemberStatus
from .serializers import IndividualLoanSerializer, GroupLoanSerializer, GroupMemberStatusSerializer
from .permissions import IsLoanOfficerOrHigher
from core import serializers

class IndividualLoanViewSet(viewsets.ModelViewSet):
    queryset = IndividualLoan.objects.all().order_by('-created_at')
    serializer_class = IndividualLoanSerializer
    permission_classes = [IsAuthenticated, IsLoanOfficerOrHigher]

    def perform_create(self, serializer):
        serializer.save(loan_officer=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role in ['superuser', 'manager', 'region_manager']:
            return self.queryset
        elif user.role == 'loan_officer':
            return self.queryset.filter(loan_officer=user)
        else:
            return self.queryset.filter(recipient=user)

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