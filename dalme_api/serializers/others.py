from django.contrib.auth.models import Group

from dalme_app.models import (Attribute_type, Attachment, Content_attributes, Content_class, CountryReference,
                              GroupProperties, Profile, Tag, Transcription)

from rest_framework import serializers
from ._common import DynamicSerializer


class AttachmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attachment
        fields = ('filename', 'source', 'type')


class AttributeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute_type
        fields = ('id', 'name', 'short_name', 'description', 'data_type', 'source', 'options_list', 'same_as')


class ContentClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content_class
        fields = ('id', 'name', 'short_name', 'description')


class ContentXAttributeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='attribute_type.id')
    name = serializers.CharField(max_length=255, source='attribute_type.name')
    short_name = serializers.CharField(max_length=55, source='attribute_type.short_name')
    description = serializers.CharField(source='attribute_type.description')
    data_type = serializers.CharField(max_length=15, source='attribute_type.data_type')
    source = serializers.CharField(max_length=255, source='attribute_type.source')
    same_as = serializers.PrimaryKeyRelatedField(source='attribute_type.same_as', read_only=True)
    options_list = serializers.CharField(max_length=255, source='attribute_type.options_list')
    required = serializers.BooleanField()

    class Meta:
        model = Content_attributes
        fields = ('id', 'name', 'short_name', 'description', 'data_type', 'source', 'same_as', 'options_list', 'required')


class CountryReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryReference
        fields = ('id', 'name', 'alpha_2_code', 'alpha_3_code', 'num_code')


class GroupPropertiesSerializer(DynamicSerializer):
    class Meta:
        model = GroupProperties
        fields = ('type', 'description')


class GroupSerializer(DynamicSerializer):
    """ Basic serializer for user group data """
    properties = GroupPropertiesSerializer(required=False)
    description = serializers.CharField(max_length=255, source='properties.description', required=False)

    class Meta:
        model = Group
        fields = ('id', 'name', 'properties', 'description')
        extra_kwargs = {'name': {'required': False}, }


class ProfileSerializer(DynamicSerializer):
    """ Serialises user profiles """
    primary_group = GroupSerializer(fields=['name', 'id', 'description'], required=False)

    class Meta:
        model = Profile
        fields = ('full_name', 'primary_group')


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tag data """
    tag_type_name = serializers.ChoiceField(choices=Tag.TAG_TYPES, source='get_tag_type_display', required=False)

    class Meta:
        model = Tag
        fields = ('tag_type', 'tag', 'tag_group', 'tag_type_name')
        extra_kwargs = {'tag_type': {'required': False}}


class TranscriptionSerializer(serializers.ModelSerializer):
    """ Basic serializer for transcriptions """
    author = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = Transcription
        fields = ('id', 'transcription', 'author', 'version')
