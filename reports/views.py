from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import (
    PaymentsCollectedReport,
    ActiveGroupsReport,
    AmountLoanedReport,
    ActiveLoansReport
)
from .serializers import (
    PaymentsCollectedReportSerializer,
    ActiveGroupsReportSerializer,
    AmountLoanedReportSerializer,
    ActiveLoansReportSerializer
)
from users.permissions import IsRegionManagerOrHigher

class PaymentsCollectedViewSet(viewsets.ModelViewSet):
    queryset = PaymentsCollectedReport.objects.all()
    serializer_class = PaymentsCollectedReportSerializer
    permission_classes = [IsAuthenticated, IsRegionManagerOrHigher]

class ActiveGroupsViewSet(viewsets.ModelViewSet):
    queryset = ActiveGroupsReport.objects.all()
    serializer_class = ActiveGroupsReportSerializer
    permission_classes = [IsAuthenticated, IsRegionManagerOrHigher]

class AmountLoanedViewSet(viewsets.ModelViewSet):
    queryset = AmountLoanedReport.objects.all()
    serializer_class = AmountLoanedReportSerializer
    permission_classes = [IsAuthenticated, IsRegionManagerOrHigher]

class ActiveLoansViewSet(viewsets.ModelViewSet):
    queryset = ActiveLoansReport.objects.all()
    serializer_class = ActiveLoansReportSerializer
    permission_classes = [IsAuthenticated, IsRegionManagerOrHigher]