from django.contrib.auth.models import User, Group, Permission
from rest_framework import serializers

class PermissionSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for django.contrib.auth.models.Permission
    """
    content_type = serializers.StringRelatedField()

    class Meta:
        model = Permission
        fields = '__all__'
        extra_kwargs = {
                'url': {'view_name': 'permissions-detail-api'}
                }

class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class for django.contrib.auth.models.User
    """
    groups = serializers.HyperlinkedRelatedField(
            many=True,
            read_only=True,
            view_name='groups-detail-api'
            )
    user_permissions = serializers.HyperlinkedRelatedField(
            many=True,
            read_only=True,
            view_name='permissions-detail-api'
            )

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'url': {'view_name': 'users-detail-api'}
            }

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer class django.contrib.auth.models.Group
    """
    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {
                'url': {'view_name': 'groups-detail-api'}
                }
