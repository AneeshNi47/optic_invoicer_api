from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Staff
from accounts.models import Invitation
from .serializers import StaffSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StaffSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_invitation(request):
    # Ensure the request user has the necessary permissions
    if not request.user.staff.staff_superuser:
        return Response({'detail': 'Only super staff can send invitations.'}, status=status.HTTP_403_FORBIDDEN)
    
    email = request.data.get('email')
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the email already exists
    if User.objects.filter(email=email).exists():
        return Response({'detail': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the invitation
    invitation = Invitation(email=email, created_by=request.user)
    invitation.save()
    invitation.send_invitation()

    return Response({'detail': 'Invitation sent successfully.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_staff(request, token):
    try:
        invitation = Invitation.objects.get(token=token)
    except Invitation.DoesNotExist:
        return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

    # Extract the required data
    email = invitation.email
    password = request.data.get('password')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    designation = request.data.get('designation')
    phone = request.data.get('phone')
    
    # Create the user account
    user = User.objects.create_user(username=email, email=email, password=password)
    
    # Create the staff object
    staff = Staff.objects.create(user=user, first_name=first_name, last_name=last_name, designation=designation, phone=phone)
    
    # Mark the invitation as accepted
    invitation.accepted_at = timezone.now()
    invitation.status = 'accepted'
    invitation.save()

    return Response({'detail': 'Staff registered successfully.'}, status=status.HTTP_201_CREATED)
