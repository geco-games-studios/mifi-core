from datetime import timedelta
from decimal import Decimal
from django.db import models
from users.models import User
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

def photo_upload_path(instance, filename):
    return f"collateral/photos/loan_{instance.loan.id}/{filename}"

def video_upload_path(instance, filename):
    return f"collateral/videos/loan_{instance.loan.id}/{filename}"

class Loan(models.Model):
    LOAN_TYPES = (
        ('individual', 'Individual'),
        ('group', 'Group'),
    )
    
    LOAN_STATUSES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed'),
    )
    
    REPAYMENT_FREQUENCIES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40.0,  # Fixed at 40%
        # editable=False  # Makes it non-editable in admin and forms
    )
    repayment_frequency = models.CharField(
        max_length=10,
        choices=REPAYMENT_FREQUENCIES,
        default='weekly',
        help_text="How often payments are due"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    loan_officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_loans'
    )
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=LOAN_STATUSES, 
        default='active'
    )


    def calculate_interest(self):
        duration_days = (self.end_date - self.start_date).days
        if duration_days <= 0:
            return Decimal('0.00')
        
        # Fixed interest rate of 40%
        interest_rate = Decimal('40.0')
        
        # Calculate based on repayment frequency
        if self.repayment_frequency == 'daily':
            # For daily loans, interest is calculated per day
            interest_per_day = (self.amount * interest_rate) / (100 * 365)
            return round(interest_per_day * duration_days, 2)
        
        elif self.repayment_frequency == 'weekly':
            # For weekly loans, interest is calculated per week
            weeks = duration_days / 7
            interest_per_week = (self.amount * interest_rate) / (100 * 52)
            return round(interest_per_week * weeks, 2)
        
        elif self.repayment_frequency == 'monthly':
            # For monthly loans, interest is calculated per month
            months = duration_days / 30  # Approximate
            interest_per_month = (self.amount * interest_rate) / (100 * 12)
            return round(interest_per_month * months, 2)

    def get_payment_schedule(self):
        """
        Generate a payment schedule based on repayment frequency
        Returns a list of (date, amount) tuples
        """
        schedule = []
        current_date = self.start_date
        total_installments = self.get_total_installments()
        installment_amount = self.total_due / total_installments
        
        while current_date <= self.end_date:
            schedule.append((current_date, installment_amount))
            
            if self.repayment_frequency == 'daily':
                current_date += timedelta(days=1)
            elif self.repayment_frequency == 'weekly':
                current_date += timedelta(weeks=1)
            elif self.repayment_frequency == 'monthly':
                # Handle month increments properly
                next_month = current_date.month + 1
                next_year = current_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                try:
                    current_date = current_date.replace(month=next_month, year=next_year)
                except ValueError:
                    # Handle cases where day doesn't exist in next month
                    current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=current_date.day)
        
        return schedule

    def get_total_installments(self):
        """Calculate total number of installments based on frequency"""
        duration_days = (self.end_date - self.start_date).days
        
        if self.repayment_frequency == 'daily':
            return duration_days
        elif self.repayment_frequency == 'weekly':
            return int(duration_days / 7)
        elif self.repayment_frequency == 'monthly':
            return int(duration_days / 30)  # Approximation
        
        return 1

    def save(self, *args, **kwargs):
        # On creation, set total_due = amount if not already set
        if self.pk is None and not self.total_due:
            self.total_due = self.amount
        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
        
        # Check that both dates are present
        if self.start_date is None or self.end_date is None:
            raise ValidationError("Both start date and end date are required.")
            
        # Validate loan duration doesn't exceed 28 days
        if (self.end_date - self.start_date).days > 28:
            raise ValidationError("Loan duration cannot exceed 28 days.")
            
        # Validate end date is after start date
        if self.end_date < self.start_date:
            raise ValidationError("End date must be after start date.")
        

    class Meta:
        abstract = True

class IndividualLoan(Loan):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='individual_loans_as_recipient'
    )
    REQUIRED_COLLATERAL_TYPES = ['PHOTO']  # At least one photo required

    def save(self, *args, **kwargs):
        # Set status to active if it's a new loan and status isn't set
        if not self.pk and not self.status:
            self.status = 'active'
        super().save(*args, **kwargs)

        skip_collateral_check = kwargs.pop('skip_collateral_check', False)
        
        if not skip_collateral_check and not self.pk:
            # New loan - we'll validate after save when adding collaterals
            super().save(*args, **kwargs)
        else:
            self.clean()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.amount} - {self.get_status_display()}"
    

    def make_payment(self, amount, user, member=None):
        if amount <= 0:
            raise ValidationError("Payment amount must be positive.")
            
        if amount > self.total_due:
            raise ValidationError("Payment amount exceeds total due.")
            
        self.total_due -= amount
        self.total_paid += amount
        self.save()
        
        if isinstance(self, IndividualLoan):
            return IndividualLoanPayment.objects.create(
                loan=self,
                amount=amount,
                recorded_by=user
            )
        elif isinstance(self, GroupLoan) and member:
            return GroupLoanPayment.objects.create(
                loan=self,
                amount=amount,
                recorded_by=user,
                member=member
            )
        else:
            raise ValidationError("Invalid payment parameters.")
        
    def make_normal_payment(self, amount, user):
        if self.status != 'ACTIVE':
            raise ValidationError("Payments can only be made on active loans")
            
        payment = IndividualLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            payment_type='NORMAL'
        )
        self.balance -= amount
        self.save()
        return payment
    
    def make_advance_payment(self, amount, user):
        if self.status != 'ACTIVE':
            raise ValidationError("Payments can only be made on active loans")
        if self.get_next_due_payment():  # If there are pending payments
            raise ValidationError("Advance payments can only be made when there are no pending payments")
            
        payment = IndividualLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            payment_type='ADVANCE'
        )
        self.balance -= amount
        self.save()
        return payment
    
    def make_recovery_payment(self, amount, user):
        if self.status != 'OVERDUE':
            raise ValidationError("Recovery payments can only be made on overdue loans")
            
        payment = IndividualLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            payment_type='RECOVERY'
        )
        self.balance -= amount
        if self.balance <= 0:
            self.status = 'PAID'
        self.save()
        return payment
    
    
    
    def clean(self):
        super().clean()
        
        # If this is an existing loan and we're updating it
        if self.pk:
            existing_collaterals = self.collaterals.all()
            collateral_types = existing_collaterals.values_list('collateral_type', flat=True)
            
            # Check if all required collateral types are present
            for required_type in self.REQUIRED_COLLATERAL_TYPES:
                if required_type not in collateral_types:
                    raise ValidationError(
                        f"Required collateral type {required_type} is missing"
                    )
    
    def save(self, *args, **kwargs):
        # Skip collateral validation when creating via admin or other special cases
        skip_collateral_check = kwargs.pop('skip_collateral_check', False)
        
        if not skip_collateral_check and not self.pk:
            # New loan - we'll validate after save when adding collaterals
            super().save(*args, **kwargs)
        else:
            self.clean()
            super().save(*args, **kwargs)

class GroupMemberStatus(models.Model):
    group_loan = models.ForeignKey('GroupLoan', on_delete=models.CASCADE)
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_member_statuses'
    )
    frequency_letter = models.CharField(
        max_length=1,
        help_text="Letter representing frequency group"
    )
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_memberships'
    )

    
    def save(self, *args, **kwargs):
        # Automatically set frequency_letter from parent group if not set
        if not self.frequency_letter and self.group_loan_id:
            self.frequency_letter = self.group_loan.frequency_letter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.email} - Group {self.frequency_letter}"
    
    class Meta:
        unique_together = ('group_loan', 'member', 'frequency_letter')
        verbose_name_plural = 'Group Member Statuses'

def collateral_upload_path(instance, filename):
    if instance.content_type.model == 'individualloan':
        return f"collaterals/individual_loans/{instance.object_id}/{instance.collateral_type.lower()}/{filename}"
    else:
        return f"collaterals/group_loans/{instance.object_id}/{instance.collateral_type.lower()}/{filename}"
class Collateral(models.Model):
    COLLATERAL_TYPES = (
        ('PHOTO', 'Photo'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
    )   
    # Generic foreign key approach
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    loan = GenericForeignKey('content_type', 'object_id')
    collateral_type = models.CharField(
        max_length=10, 
        choices=COLLATERAL_TYPES,
        help_text="Type of collateral being uploaded"
    )
    file = models.FileField(upload_to=collateral_upload_path)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_collaterals'
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_collaterals'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    

class GroupLoan(Loan):
    FREQUENCY_LETTERS = (
        ('A', 'Frequency A'),
        ('B', 'Frequency B'),
        ('C', 'Frequency C'),
        ('D', 'Frequency D'),
        ('E', 'Frequency E'),
    )
    
    # FREQUENCY_TYPES = (
    #     ('weekly', 'Weekly'),
    #     ('monthly', 'Monthly'),
    #     ('quarterly', 'Quarterly'),
    # )
    
    group_name = models.CharField(max_length=100)
    frequency_letter = models.CharField(
        max_length=1, 
        choices=FREQUENCY_LETTERS,
        help_text="Letter representing frequency group (A, B, C, etc.)"
    )
    # frequency_type = models.CharField(
    #     max_length=20, 
    #     choices=FREQUENCY_TYPES,
    #     help_text="Type of frequency (weekly, monthly, quarterly)"
    # )
    total_group_loan = models.DecimalField(max_digits=12, decimal_places=2)
    loan_given = models.BooleanField(default=False)
    due_date = models.DateField()
    transferred = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    new = models.BooleanField(default=True)
    members = models.ManyToManyField(User,through='GroupMemberStatus',through_fields=('group_loan', 'member'),related_name='group_loans')
    time = models.CharField(max_length=100, blank=True, null=True)


    def clean(self):
        super().clean()
        # Remove the members check from clean() since we'll validate in serializer

    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.group_name} - {self.total_group_loan} (Group {self.frequency_letter})"

    @property
    def full_frequency(self):
        """Returns a combined frequency representation"""
        return f"{self.frequency_letter}"
    
    def make_normal_payment(self, amount, user, member):
        if self.status != 'ACTIVE':
            raise ValidationError("Payments can only be made on active loans")
            
        payment = GroupLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            member=member,
            payment_type='NORMAL'
        )
        self.balance -= amount
        self.save()
        return payment
    
    def make_advance_payment(self, amount, user, member):
        if self.status != 'ACTIVE':
            raise ValidationError("Payments can only be made on active loans")
        if self.get_next_due_payment():  # If there are pending payments
            raise ValidationError("Advance payments can only be made when there are no pending payments")
            
        payment = GroupLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            member=member,
            payment_type='ADVANCE'
        )
        self.balance -= amount
        self.save()
        return payment
    
    def make_recovery_payment(self, amount, user, member):
        if self.status != 'OVERDUE':
            raise ValidationError("Recovery payments can only be made on overdue loans")
            
        payment = GroupLoanPayment.objects.create(
            loan=self,
            amount=amount,
            recorded_by=user,
            member=member,
            payment_type='RECOVERY'
        )
        self.balance -= amount
        if self.balance <= 0:
            self.status = 'PAID'
        self.save()
        return payment
    
class Payment(models.Model):
    """Model to track loan payments"""
    PAYMENT_TYPES = (
        ('ADVANCE', 'Advance Payment'),
        ('NORMAL', 'Normal Payment'),
        ('RECOVERY', 'Recovery Payment'),
    )
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default='NORMAL')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_recorded_payments'
    )
    
    class Meta:
        abstract = True

class IndividualLoanPayment(Payment):
    loan = models.ForeignKey(
        IndividualLoan,
        on_delete=models.CASCADE,
        related_name='payments'
    )

class GroupLoanPayment(Payment):
    loan = models.ForeignKey(
        GroupLoan,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_loan_payments'
    )