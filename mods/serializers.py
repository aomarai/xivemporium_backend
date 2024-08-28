from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import Mod, ModCompatibility, Tag, Race, Gender, Download, Rating, Comment


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "user", "text", "comment_date"]


class DownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Download
        fields = ["id", "user", "download_date"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "user", "rating"]


class ModSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    downloads = DownloadSerializer(source="mod_downloads", many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Mod
        fields = "__all__"

    def create(self, validated_data):
        category = validated_data.pop("category", None)
        tags = validated_data.pop("tags", [])

        # Create the mod instance first
        mod = Mod(**validated_data)
        mod.category = category
        mod.save()

        # Assign tags
        mod.tags.set(tags)

        # Now perform custom validations that depend on the category being set
        try:
            mod.full_clean()  # This will trigger validation including the custom validation in save()
        except ValidationError as e:
            # Delete the created mod if validation fails to maintain database integrity
            mod.delete()
            raise e

        return mod


class ModCatalogCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mod
        fields = ["title", "short_desc", "thumbnail", "category", "downloads", "upload_date", "updated_date", "user"]


class ModCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModCompatibility
        fields = ["mod", "race", "gender"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class RaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = "__all__"


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = "__all__"
