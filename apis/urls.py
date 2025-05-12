from django.contrib import admin
from django.urls import path
from core.views import GroupLoanPaymentViewSet, IndividualLoanPaymentViewSet, IndividualLoanViewSet, GroupLoanViewSet, GroupMemberStatusViewSet
from core.views import GroupLoanPaymentViewSet, IndividualLoanPaymentViewSet, IndividualLoanViewSet, GroupLoanViewSet, GroupMemberStatusViewSet
from users.views import UserViewSet
from reports.views import PaymentsCollectedViewSet,ActiveGroupsViewSet,AmountLoanedViewSet,ActiveLoansViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.serializers import CustomTokenObtainPairSerializer



urlpatterns = [

    #loans
    path('individual/', IndividualLoanViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='individual-loan-list'),
    path('individual/<int:pk>/', IndividualLoanViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='individual-loan-detail'),
    path('individual/payments/<int:loan_id>/', IndividualLoanPaymentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='individual-loan-payments'),
    path('individual/<int:loan_id>/payments/<int:pk>/', IndividualLoanPaymentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='individual-loan-payment-detail'),


    path('individual/payments/<int:loan_id>/', IndividualLoanPaymentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='individual-loan-payments'),
    path('individual/<int:loan_id>/payments/<int:pk>/', IndividualLoanPaymentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='individual-loan-payment-detail'),


    path('group/', GroupLoanViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='group-loan-list'),
    path('group/<int:pk>/', GroupLoanViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='group-loan-detail'),
    path('group/<int:loan_id>/payments/<int:pk>/', GroupLoanPaymentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='group-loan-payment-detail'),


    path('group/<int:loan_id>/payments/', GroupLoanPaymentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='group-loan-payments'),
    path('group/<int:loan_id>/payments/<int:pk>/', GroupLoanPaymentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='group-loan-payment-detail'),

    path('group-members/', GroupMemberStatusViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='group-member-list'),
    path('group-members/<int:pk>/', GroupMemberStatusViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='group-member-detail'),

    #users
    path('admin/', admin.site.urls),
    path('token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', UserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='user-list'),
    path('users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='user-detail'),

    #reports
    path('payments-collected/', PaymentsCollectedViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='payments-collected'),
    path('payments-collected/<int:pk>/', PaymentsCollectedViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='payments-collected-detail'),
    
    path('active-groups/', ActiveGroupsViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='active-groups'),
    path('active-groups/<int:pk>/', ActiveGroupsViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='active-groups-detail'),
    
    path('amount-loaned/', AmountLoanedViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='amount-loaned'),
    path('amount-loaned/<int:pk>/', AmountLoanedViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='amount-loaned-detail'),
    
    path('active-loans/', ActiveLoansViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='active-loans'),
    path('active-loans/<int:pk>/', ActiveLoansViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='active-loans-detail'),
]