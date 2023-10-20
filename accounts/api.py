from rest_framework import  permissions, generics, status
from rest_framework.response import Response
from knox.models import AuthToken
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User

from .serializers import LoginSerializer, UserSerializer

class LoginApi(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract the user instance from the validated data
        username = serializer.validated_data['username']
        user = User.objects.get(username=username)

        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


# Get User API
class UserApi(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        # Check if the user is associated with a Staff or Customer object
        if not (hasattr(request.user, 'staff') or hasattr(request.user, 'customer')):
            # Log out the user
            auth_logout(request)
            return Response({"detail": "User not associated with Staff or Customer."}, status=status.HTTP_403_FORBIDDEN)
        
        # If associated, return the user details
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def get_object(self):
        return self.request.user