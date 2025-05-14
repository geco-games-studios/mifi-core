from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import GroupLoanPayment, IndividualLoan, GroupLoan, GroupMemberStatus, IndividualLoanPayment, Collateral
from users.serializers import UserSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

class GroupLoanPaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    member = UserSerializer(read_only=True)
    
    class Meta:
        model = GroupLoanPayment
        fields = '__all__'
        read_only_fields = ('payment_date', 'recorded_by')

class IndividualLoanPaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = IndividualLoanPayment
        fields = '__all__'
        read_only_fields = ('payment_date', 'recorded_by')

class IndividualLoanPaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = IndividualLoanPayment
        fields = '__all__'
        read_only_fields = ('payment_date', 'recorded_by')

class GroupLoanPaymentSerializer(serializers.ModelSerializer):
    recorded_by = UserSerializer(read_only=True)
    member = UserSerializer(read_only=True)
    
    class Meta:
        model = GroupLoanPayment
        fields = '__all__'
        read_only_fields = ('payment_date', 'recorded_by')

class IndividualLoanSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True)
    loan_officer = UserSerializer(read_only=True)
    payments = IndividualLoanPaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = IndividualLoan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'loan_type', 'loan_officer', 'total_due', 'total_paid')

    def validate(self, data):
        data['loan_type'] = 'individual'
        return data

class GroupMemberStatusSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    blocked_by = UserSerializer(read_only=True)
    group_loan = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = GroupMemberStatus
        fields = '__all__'
        read_only_fields = ('blocked_at', 'frequency_letter')

class GroupLoanSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    member_statuses = GroupMemberStatusSerializer(many=True, read_only=True)
    loan_officer = UserSerializer(read_only=True)
    member_ids = serializers.ListField(child=serializers.IntegerField(),write_only=True,required=True,help_text="List of member user IDs (minimum 2 required)")
    frequency_letter = serializers.ChoiceField(choices=GroupLoan.FREQUENCY_LETTERS)
    payments = GroupLoanPaymentSerializer(many=True, read_only=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    
    
    
    class Meta:
        model = GroupLoan
        fields = [
            'id', 'loan_type', 'group_name', 'frequency_letter', "end_date", "start_date",
            'amount', 'penalty', 'total_group_loan', 'loan_given', "time",
            'due_date', 'transferred', 'blocked', 'new', 'members',
            'member_statuses', 'loan_officer', 'created_at', 'updated_at', 'member_ids', 'payments'
        ]

        read_only_fields = (
            'created_at', 'updated_at', 'members', 'member_statuses',
            'loan_type', 'loan_officer'
        )

    def validate(self, data):
        data['loan_type'] = 'group'
        if 'member_ids' not in data:
            raise serializers.ValidationError({"member_ids": "This field is required."})
        if len(data['member_ids']) < 2:
            raise serializers.ValidationError({"member_ids": "At least 2 members are required."})
        return data

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids')
        group_loan = GroupLoan.objects.create(**validated_data)
        
        for member_id in member_ids:
            GroupMemberStatus.objects.create(
                group_loan=group_loan,
                member_id=member_id,
                frequency_letter=group_loan.frequency_letter
            )
        
        return group_loan

    def update(self, instance, validated_data):
        member_ids = validated_data.pop('member_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if member_ids is not None:
            if len(member_ids) < 2:
                raise serializers.ValidationError({"member_ids": "At least 2 members are required."})
            
            instance.members.clear()
            for member_id in member_ids:
                GroupMemberStatus.objects.create(
                    group_loan=instance,
                    member_id=member_id,
                    frequency_letter=instance.frequency_letter
                )
        
        return instance
    
class CollateralSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by = UserSerializer(read_only=True)
    loan_type = serializers.CharField(write_only=True, required=False)  # Make optional
    loan_id = serializers.IntegerField(write_only=True, required=False)  # Make optional
    
    class Meta:
        model = Collateral
        fields = [
            'id', 'loan_type', 'loan_id', 'collateral_type', 
            'file', 'file_url', 'description', 'uploaded_at', 'verified',
            'verified_by', 'verified_at', 'uploaded_by',
        ]
        read_only_fields = [
            'id', 'file_url', 'uploaded_at', 'verified_at',
            'verified_by', 'uploaded_by'
        ]

    def get_file_url(self, obj):
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None
    
    def create(self, validated_data):
        loan_type = validated_data.pop('loan_type', None)
        loan_id = validated_data.pop('loan_id', None)
        
        user = self.context['request'].user
        
        # Create collateral without loan association if no loan info provided
        if not loan_type or not loan_id:
            return Collateral.objects.create(
                uploaded_by=user,
                **validated_data
            )
        
        # Otherwise create with loan association
        if loan_type.upper() == 'INDIVIDUAL':
            model = IndividualLoan
        elif loan_type.upper() == 'GROUP':
            model = GroupLoan
        
        content_type = ContentType.objects.get_for_model(model)
        
        return Collateral.objects.create(
            content_type=content_type,
            object_id=loan_id,
            uploaded_by=user,
            **validated_data
        )

    def validate(self, data):
        loan_type = data.get('loan_type')
        loan_id = data.get('loan_id')
        
        # If neither is provided, that's fine - we'll create unattached collateral
        if not loan_type and not loan_id:
            return data
            
        # If one is provided without the other, that's an error
        if not loan_type or not loan_id:
            raise serializers.ValidationError(
                "Both loan_type and loan_id must be provided together or omitted together"
            )
        
        # Validate loan type
        if loan_type.upper() == 'INDIVIDUAL':
            model = IndividualLoan
        elif loan_type.upper() == 'GROUP':
            model = GroupLoan
        else:
            raise serializers.ValidationError({
                'loan_type': 'Must be either INDIVIDUAL or GROUP'
            })
        
        # Validate loan exists
        try:
            loan = model.objects.get(pk=loan_id)
        except model.DoesNotExist:
            raise serializers.ValidationError({
                'loan_id': 'Loan not found'
            })
        
        # Validate loan status
        if loan.status not in ['active', 'pending']:
            raise serializers.ValidationError(
                "Collateral can only be added to active or pending loans"
            )
        
        return data
    
