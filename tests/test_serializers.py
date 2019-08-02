from collections import OrderedDict

from django.contrib.auth.models import Group, User
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
        self.writer = create('writer', password='password')
        self.reader = create('reader', password='password')
        self.no_perms = create('no_perms', password='password')

        # Add readers to our reader group
        reader_group = Group.objects.create(name='readers')
        reader_group.user_set.add(self.reader)

    def create_object(self):
        request = factory.post('/')
        request.user = self.writer

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

        self.assertTrue(self.writer.has_perm('view_basicmodel', instance))
        # check if readers group members have view perm
        self.assertTrue(self.reader.has_perm('view_basicmodel', instance))

    def test_can_change_assigned_objects(self):
        instance = self.create_object()

        self.assertTrue(self.writer.has_perm('change_basicmodel', instance))

    def test_cannot_read_unassigned_objects(self):
        instance = self.create_object()

        self.assertFalse(self.no_perms.has_perm('view_basicmodel', instance))

    def test_cannot_change_unassigned_objects(self):
        instance = self.create_object()

        self.assertFalse(self.no_perms.has_perm('change_basicmodel', instance))
        # check if readers group members don't have change perm
        self.assertFalse(self.reader.has_perm('change_basicmodel', instance))

    def test_cannot_delete_unassigned_objects(self):
        instance = self.create_object()

        self.assertFalse(self.writer.has_perm('delete_basicmodel', instance))
        self.assertFalse(self.reader.has_perm('delete_basicmodel', instance))
        self.assertFalse(self.no_perms.has_perm('delete_basicmodel', instance))


class ObjectPermissionsAssignmentImplementationTests(TestCase):

    def test_get_permissions_map_should_return_a_mapping(self):
        for return_value in [dict(), OrderedDict()]:
            class TestSerializer(BasicSerializer):
                def get_permissions_map(self, created):
                    return return_value

            serializer = TestSerializer(data={'text': 'test'})
            serializer.is_valid(raise_exception=True)
            self.assertIsInstance(serializer.save(), BasicModel)

    def test_get_permissions_map_error_message(self):
        error_message = (
            'Expected InvalidSerializer.get_permissions_map '
            'to return a dict, got list instead.'
        )

        class InvalidSerializer(BasicSerializer):
            def get_permissions_map(self, created):
                return []

        serializer = InvalidSerializer(data={'text': 'test'})
        serializer.is_valid(raise_exception=True)

        with self.assertRaisesMessage(AssertionError, error_message):
            serializer.save()
