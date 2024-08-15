from rest_framework import serializers

from .models import Mod, ModCompatibility


class ModSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mod
        fields = [
            "title",
            "short_desc",
            "description",
            "version",
            "upload_date",
            "updated_date",
            "file",
            "file_size",
            "user",
            "downloads",
            "categories",
            "tags",
            "approved",
        ]


class ModCatalogCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mod
        fields = ["title", "short_desc", "thumbnail", "categories", "downloads", "upload_date", "updated_date", "user"]


class ModCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModCompatibility
        fields = ["mod", "race", "gender"]
