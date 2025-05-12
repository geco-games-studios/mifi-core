from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .permissions import CanCreateClient, IsManagerOrHigher, IsRegionManagerOrHigher

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanCreateClient]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role in ['superuser', 'manager']:
            return queryset
        elif user.role == 'region_manager':
            return queryset.filter(region=user.region)
        elif user.role == 'loan_officer':
            return queryset.filter(Q(role='clients') | Q(id=user.id))
        else:
            return queryset.filter(id=user.id)