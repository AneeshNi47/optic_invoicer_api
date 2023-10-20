from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Organization
from rest_framework.views import APIView
from .serializers import OrganizationSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return Organization.objects.filter(id=self.request.get_organization().id).first()
        else:
            # Handle unauthenticated users
            return Organization.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise serializer.ValidationError("Only superusers can create an organization.")
        serializer.save(owner=self.request.user)

class GetOrganizationView(APIView):
    """
    Get the User Current Organization.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        organization = Organization.objects.filter(id=request.get_organization().id).first()
        if organization:
            serializer = OrganizationSerializer(organization)
            return Response(serializer.data)
        else:
             return Response({'detail': 'Organization not found for the user.'}, status=status.HTTP_404_NOT_FOUND)