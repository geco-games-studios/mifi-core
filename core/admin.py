from django.contrib import admin
from .models import (
    IndividualLoan,
    GroupLoan,
    GroupMemberStatus,
    IndividualLoanPayment,
    GroupLoanPayment
)

# Define the inline class first
class GroupMemberStatusInline(admin.TabularInline):
    model = GroupMemberStatus
    extra = 1
    raw_id_fields = ('member', 'blocked_by')
    readonly_fields = ('blocked_at',)

@admin.register(IndividualLoan)
class IndividualLoanAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'recipient', 'amount', 'loan_type', 
                    'start_date', 'end_date', 'total_due', 'total_paid', 'loan_officer')
    list_filter = ('loan_type', 'start_date', 'end_date')
    search_fields = ('first_name', 'last_name', 'recipient__email')
    raw_id_fields = ('recipient', 'loan_officer')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_due', 'total_paid')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('loan_type', 'first_name', 'last_name', 'recipient', 'loan_officer')
        }),
        ('Loan Details', {
            'fields': ('amount', 'penalty', 'start_date', 'end_date')
        }),
        ('Financials', {
            'fields': ('total_due', 'total_paid')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(GroupLoan)
class GroupLoanAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'frequency_letter', 'amount', 'loan_type', 
                    'start_date', 'end_date', 'total_due', 'total_paid', 'loan_officer')
    list_filter = ('frequency_letter', 'start_date', 'end_date', 'loan_given')
    search_fields = ('group_name', 'loan_officer__email')
    raw_id_fields = ('loan_officer',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'total_due', 'total_paid')
    inlines = [GroupMemberStatusInline]  # Now properly defined
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('loan_type', 'group_name', 'frequency_letter', 'loan_officer')
        }),
        ('Loan Details', {
            'fields': ('amount', 'penalty', 'start_date', 'end_date', 'due_date')
        }),
        ('Status Flags', {
            'fields': ('loan_given', 'transferred', 'blocked', 'new'),
            'classes': ('collapse',)
        }),
        ('Financials', {
            'fields': ('total_due', 'total_paid')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(GroupMemberStatus)
class GroupMemberStatusAdmin(admin.ModelAdmin):
    list_display = ('member', 'group_loan', 'frequency_letter', 'is_blocked', 'blocked_at')
    list_filter = ('frequency_letter', 'is_blocked')
    search_fields = ('member__email', 'group_loan__group_name')
    raw_id_fields = ('member', 'group_loan', 'blocked_by')
    
    fieldsets = (
        (None, {
            'fields': ('member', 'group_loan', 'frequency_letter')
        }),
        ('Block Status', {
            'fields': ('is_blocked', 'blocked_at', 'blocked_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(IndividualLoanPayment)
class IndividualLoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'payment_date', 'recorded_by')
    list_filter = ('payment_date',)
    search_fields = ('loan__first_name', 'loan__last_name', 'recorded_by__email')
    raw_id_fields = ('loan', 'recorded_by')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (None, {
            'fields': ('loan', 'amount', 'recorded_by')
        }),
        ('Metadata', {
            'fields': ('payment_date',),
            'classes': ('collapse',)
        }),
    )

@admin.register(GroupLoanPayment)
class GroupLoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'member', 'amount', 'payment_date', 'recorded_by')
    list_filter = ('payment_date', 'loan__frequency_letter')
    search_fields = ('loan__group_name', 'member__email', 'recorded_by__email')
    raw_id_fields = ('loan', 'member', 'recorded_by')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (None, {
            'fields': ('loan', 'member', 'amount', 'recorded_by')
        }),
        ('Metadata', {
            'fields': ('payment_date',),
            'classes': ('collapse',)
        }),
    )