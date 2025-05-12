from django.db import models
from users.models import User
from django.core.exceptions import ValidationError




class Loan(models.Model):
    LOAN_TYPES = (
        ('individual', 'Individual'),
        ('group', 'Group'),
    )
    
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # time = models.IntegerField()  # in months
    penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
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
    
    def clean(self):
        # Validate loan duration doesn't exceed 28 days
        if (self.end_date - self.start_date).days > 28:
            raise ValidationError("Loan duration cannot exceed 28 days.")
        
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

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.amount}"

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
    
    class Meta:
        unique_together = ('group_loan', 'member', 'frequency_letter')
        verbose_name_plural = 'Group Member Statuses'

    def save(self, *args, **kwargs):
        # Automatically set frequency_letter from parent group if not set
        if not self.frequency_letter and self.group_loan_id:
            self.frequency_letter = self.group_loan.frequency_letter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.email} - Group {self.frequency_letter}"

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
    
class Payment(models.Model):
    """Model to track loan payments"""
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_recorded_payments'  # This will make it unique per child class
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