from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'role', 'phone_number', 'address', 'region',
            'nrc_number', 'date_of_birth'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'read_only': True}  # Role should be set by the system, not client
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_staff:
            raise serializers.ValidationError("Only staff members can create users.")
        
        # For clients created by loan officers
        if request.user.role in ['loan_officer', 'region_manager', 'manager', 'superuser']:
            validated_data['role'] = 'clients'
        
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token