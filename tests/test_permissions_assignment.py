
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import authentication, serializers, status, viewsets
from rest_framework.test import APIRequestFactory

from rest_framework_guardian.filters import DjangoObjectPermissionsFilter
from rest_framework_guardian.serializers import DjangoGuardianObjectPermissionsAssigner
from tests.models import BasicModel
from tests.permissions import ViewObjectPermissions
from tests.utils import basic_auth_header


factory = APIRequestFactory()


class BasicSerializer(
        DjangoGuardianObjectPermissionsAssigner,
        serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'

    def get_permissions_map(self, created):
        current_user = self.context['request'].user
        readers = Group.objects.get(name='readers')

        return {
            'view_%s' % BasicModel._meta.model_name: [current_user, readers],
            'change_%s' % BasicModel._meta.model_name: [current_user],
        }


class BasicViewSet(viewsets.ModelViewSet):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [ViewObjectPermissions]
    filter_backends = [DjangoObjectPermissionsFilter]


class ObjectPermissionsAssignmentIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions assignment API.
    """

    def setUp(self):
        from guardian.shortcuts import assign_perm

        # create users
        create = User.objects.create_user
        users = {
            'user1': create('user1', 'user1@example.com', 'password'),
            'user2': create('user2', 'user2@example.com', 'password'),
            'user3': create('user3', 'user2@example.com', 'password'),
        }

        model_name = BasicModel._meta.model_name
        app_label = BasicModel._meta.app_label

        # give everyone model level permissions, as we are not testing those
        everyone = Group.objects.create(name='everyone')
        everyone.user_set.add(*users.values())

        for action in ('add', 'view', 'change', 'delete'):
            perm = '{0}.{1}_{2}'.format(app_label, action, model_name)
            assign_perm(perm, everyone)

        # readers are supposed to get `view` permission by the assigner
        readers = Group.objects.create(name='readers')
        readers.user_set.add(users['user3'])

        perm = '{0}.{1}_{2}'.format(app_label, 'view', model_name)
        assign_perm(perm, readers)

        self.credentials = {}
        for user in users.values():
            self.credentials[user.username] = basic_auth_header(user.username, 'password')

    def request(self, method, action, username, data=None, pk=None):
        """
        A shortcut function to facilitate requests to BasicViewSet
        """

        request = getattr(factory, method)(
            '/',
            data,
            HTTP_AUTHORIZATION=self.credentials[username],
        )
        view = BasicViewSet.as_view({
            method: action,
        })
        return view(request, pk=pk)

    def create_object(self):
        response = self.request(
            'post',
            'create',
            'user1',
            data={
                'text': 'hello world',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_read_assigned_objects(self):
        self.create_object()

        response = self.request(
            'get',
            'list',
            'user1',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        response = self.request(
            'get',
            'list',
            'user3',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_can_change_assigned_objects(self):
        self.create_object()

        response = self.request(
            'patch',
            'partial_update',
            'user1',
            data={
                'text': 'hello world 2',
            },
            pk=1,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_read_unassigned_objects(self):
        self.create_object()

        response = self.request(
            'get',
            'list',
            'user2',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_cannot_change_unassigned_objects(self):
        self.create_object()

        response = self.request(
            'patch',
            'partial_update',
            'user2',
            data={
                'text': 'hello world 2',
            },
            pk=1,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.request(
            'patch',
            'partial_update',
            'user3',
            data={
                'text': 'hello world 3',
            },
            pk=1,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_unassigned_objects(self):
        self.create_object()

        response = self.request(
            'delete',
            'destroy',
            'user1',
            pk=1,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.request(
            'delete',
            'destroy',
            'user3',
            pk=1,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
