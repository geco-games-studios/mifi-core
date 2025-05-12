from django.db import models
from django.utils import timezone
from core.models import IndividualLoan, GroupLoan

class Report(models.Model):
    name = models.CharField(max_length=100)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True

class PaymentsCollectedReport(Report):
    start_date = models.DateField()
    end_date = models.DateField()
    total_payments = models.DecimalField(max_digits=12, decimal_places=2)
    payment_count = models.IntegerField()

class ActiveGroupsReport(Report):
    total_groups = models.IntegerField()
    active_groups = models.IntegerField()

class AmountLoanedReport(Report):
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    individual_loans_amount = models.DecimalField(max_digits=12, decimal_places=2)
    group_loans_amount = models.DecimalField(max_digits=12, decimal_places=2)

class ActiveLoansReport(Report):
    total_loans = models.IntegerField()
    active_loans = models.IntegerField()
    overdue_loans = models.IntegerField()