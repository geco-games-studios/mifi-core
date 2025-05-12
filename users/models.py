from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superuser')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLES = (
        ('clients', 'Client'),
        ('loan_officer', 'Loan Officer'),
        ('region_manager', 'Region Manager'),
        ('manager', 'Manager'),
        ('superuser', 'Super User'),
    )
    
    role = models.CharField(max_length=20, choices=ROLES, default='clients')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    nrc_number = models.CharField(max_length=30, blank=False, null=False, unique=True)  # Changed to required for all
    date_of_birth = models.DateField(blank=True, null=True)
    
    email = models.EmailField(unique=True)
    username = None

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'nrc_number']

    def clean(self):
        super().clean()
        # NRC number is now required for all users, so no need to check it here specifically
        if self.role == 'clients':
            if not all([self.first_name, self.last_name, self.date_of_birth]):
                raise ValidationError("Clients must have first name, last name, and date of birth.")
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"