from rest_framework import serializers
from .models import GroupLoanPayment, IndividualLoan, GroupLoan, GroupMemberStatus, IndividualLoanPayment
from users.serializers import UserSerializer

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
    
    class Meta:
        model = IndividualLoan
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'loan_type', 'loan_officer')

    def validate(self, data):
        data['loan_type'] = 'individual'
        return data

class GroupMemberStatusSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    blocked_by = UserSerializer(read_only=True)
    group_loan = serializers.PrimaryKeyRelatedField(read_only=True)
    payments = GroupLoanPaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = GroupLoan
        fields = [
            'payments'
        ]

    
    class Meta:
        model = GroupMemberStatus
        fields = '__all__'
        read_only_fields = ('blocked_at', 'frequency_letter')

class GroupLoanSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    member_statuses = GroupMemberStatusSerializer(many=True, read_only=True)
    loan_officer = UserSerializer(read_only=True)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="List of member user IDs (minimum 2 required)"
    )
    frequency_letter = serializers.ChoiceField(choices=GroupLoan.FREQUENCY_LETTERS)
    
    class Meta:
        model = GroupLoan
        fields = [
            'id', 'loan_type', 'group_name', 'frequency_letter',
            'amount', 'penalty', 'total_group_loan', 'loan_given',
            'due_date', 'transferred', 'blocked', 'new', 'members',
            'member_statuses', 'loan_officer', 'created_at', 'updated_at', 'member_ids'
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
    
