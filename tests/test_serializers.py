from collections import OrderedDict

from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin
from tests.models import BasicModel


factory = APIRequestFactory()


class BasicSerializer(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer):
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


class ObjectPermissionsAssignmentIntegrationTests(TestCase):
    """
    Integration tests for the object level permissions assignment API.
    """

    def setUp(self):

        create = User.objects.create_user
        self.users = {
            'writer': create('writer', 'writer@example.com', 'password'),
            'regular_user':
                create('regular_user', 'regular_user@example.com', 'password'),
            'reader': create('reader', 'reader@example.com', 'password'),
        }

        create = Group.objects.create
        self.groups = {
            'readers': create(name='readers'),
        }
        self.groups['readers'].user_set.add(self.users['reader'])

        model_name = BasicModel._meta.model_name
        self.perms = {
            'view': '{0}_{1}'.format('view', model_name),
            'change': '{0}_{1}'.format('change', model_name),
            'delete': '{0}_{1}'.format('delete', model_name),
        }

    def create_object(self):
        request = factory.post('/')
        request.user = self.users['writer']

        serializer = BasicSerializer(
            data={
                'text': 'test',
            },
            context={
                'request': request,
            },
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return instance

    def test_can_read_assigned_objects(self):
        instance = self.create_object()

        assert self.users['writer'].has_perm(self.perms['view'], instance)
        # check if readers group members have view perm
        assert self.users['reader'].has_perm(self.perms['view'], instance)

    def test_can_change_assigned_objects(self):
        instance = self.create_object()

        assert self.users['writer'].has_perm(self.perms['change'], instance)

    def test_cannot_read_unassigned_objects(self):
        instance = self.create_object()

        assert not self.users['regular_user'].has_perm(
            self.perms['view'],
            instance,
        )

    def test_cannot_change_unassigned_objects(self):
        instance = self.create_object()

        assert not self.users['regular_user'].has_perm(
            self.perms['change'],
            instance,
        )
        # check if readers group members don't have change perm
        assert not self.users['reader'].has_perm(
            self.perms['change'],
            instance,
        )

    def test_cannot_delete_unassigned_objects(self):
        instance = self.create_object()

        assert not self.users['writer'].has_perm(
            self.perms['delete'],
            instance,
        )
        assert not self.users['reader'].has_perm(
            self.perms['delete'],
            instance,
        )
        assert not self.users['regular_user'].has_perm(
            self.perms['delete'],
            instance,
        )


class ObjectPermissionsAssignmentImplementationTests(TestCase):
    def setUp(self):
        request = factory.post('/')
        request.user = AnonymousUser()

        self.serializer = BasicSerializer(
            data={
                'text': 'test',
            },
            context={
                'request': request,
            },
        )
        self.serializer.is_valid(raise_exception=True)

    def override_serializer_get_permissions_map(self, func):
        self.serializer.get_permissions_map = (
            func.__get__(
                self.serializer,
                self.serializer.__class__,
            )
        )

    def test_serializer_get_permission_map_should_return_a_mapping(self):
        return_values = (
            dict(), OrderedDict(),
        )
        for return_value in return_values:
            self.override_serializer_get_permissions_map(
                lambda self, created: return_value,
            )
            assert self.serializer.save()

    def test_serializer_get_permission_map_should_not_return_none_mapping(self):
        assertion_error_message = (
            'Expected BasicSerializer.get_permissions_map '
            'to return a dict, got %s instead.'
        )

        return_values = (
            int(), float(), list(),
            tuple(), set(), str(),
            bool(True), object(), iter([]),
        )
        for return_value in return_values:
            self.override_serializer_get_permissions_map(
                lambda self, created: return_value,
            )
            with self.assertRaisesMessage(
                    AssertionError,
                    assertion_error_message % type(return_value).__name__):
                self.serializer.save()
