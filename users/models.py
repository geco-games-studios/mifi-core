from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError

def user_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.id}/{filename}'

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
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
    nrc_number = models.CharField(max_length=30, blank=False, null=False, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)

    email = models.EmailField(unique=True)
    username = None

    # Upload fields
    nrc_front = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    nrc_back = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'nrc_number']

    def clean(self):
        super().clean()
        if self.role == 'clients':
            if not all([self.first_name, self.last_name, self.date_of_birth]):
                raise ValidationError("Clients must have first name, last name, and date of birth.")

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
