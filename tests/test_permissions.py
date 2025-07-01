from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import authentication, generics, permissions, serializers, status
from rest_framework.test import APIRequestFactory

from rest_framework_guardian.filters import ObjectPermissionsFilter
from tests.models import BasicModel, BasicPermModel
from tests.utils import basic_auth_header


factory = APIRequestFactory()


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class BasicPermSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicPermModel
        fields = '__all__'


# Custom object-level permission, that includes 'view' permissions
class ViewObjectPermissions(permissions.DjangoObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class ObjectPermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BasicPermModel.objects.all()
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]


object_permissions_view = ObjectPermissionInstanceView.as_view()


class ObjectPermissionListView(generics.ListAPIView):
    queryset = BasicPermModel.objects.all()
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]


object_permissions_list_view = ObjectPermissionListView.as_view()


class GetQuerysetObjectPermissionInstanceView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasicPermSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]

    def get_queryset(self):
        return BasicPermModel.objects.all()


get_queryset_object_permissions_view = GetQuerysetObjectPermissionInstanceView.as_view()


class ObjectPermissionsIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions API.
    """

    def setUp(self):
        from guardian.shortcuts import assign_perm

        # create users
        create = User.objects.create_user
        users = {
            'fullaccess': create('fullaccess', 'fullaccess@example.com', 'password'),
            'readonly': create('readonly', 'readonly@example.com', 'password'),
            'writeonly': create('writeonly', 'writeonly@example.com', 'password'),
            'deleteonly': create('deleteonly', 'deleteonly@example.com', 'password'),
        }

        # give everyone model level permissions, as we are not testing those
        everyone = Group.objects.create(name='everyone')
        model_name = BasicPermModel._meta.model_name
        app_label = BasicPermModel._meta.app_label
        perms = {
            'view': '{0}_{1}'.format('view', model_name),
            'change': '{0}_{1}'.format('change', model_name),
            'delete': '{0}_{1}'.format('delete', model_name),
        }
        for perm in perms.values():
            perm = '{0}.{1}'.format(app_label, perm)
            assign_perm(perm, everyone)
        everyone.user_set.add(*users.values())

        # appropriate object level permissions
        readers = Group.objects.create(name='readers')
        writers = Group.objects.create(name='writers')
        deleters = Group.objects.create(name='deleters')

        model = BasicPermModel.objects.create(text='foo')

        assign_perm(perms['view'], readers, model)
        assign_perm(perms['change'], writers, model)
        assign_perm(perms['delete'], deleters, model)

        readers.user_set.add(users['fullaccess'], users['readonly'])
        writers.user_set.add(users['fullaccess'], users['writeonly'])
        deleters.user_set.add(users['fullaccess'], users['deleteonly'])

        self.credentials = {}
        for user in users.values():
            auth = basic_auth_header(user.username, 'password')
            self.credentials[user.username] = auth

    def test_can_read_list_permissions(self):
        request = factory.get('/', HTTP_AUTHORIZATION=self.credentials['readonly'])
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get('id'), 1)

    def test_cannot_read_list_permissions(self):
        request = factory.get('/', HTTP_AUTHORIZATION=self.credentials['writeonly'])
        response = object_permissions_list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])
