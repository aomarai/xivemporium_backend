from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import Mod, ModCompatibility


class ModSerializer(serializers.ModelSerializer):
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
