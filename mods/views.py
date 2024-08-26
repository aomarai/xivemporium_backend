from rest_framework import generics

from .models import Mod, Race, Gender, Tag
from .serializers import ModSerializer, RaceSerializer, GenderSerializer, TagSerializer


class ModListAPIView(generics.ListAPIView):
    queryset = Mod.objects.filter(approved=True)
    serializer_class = ModSerializer
    lookup_field = "uuid"


class ModDetailAPIView(generics.RetrieveAPIView):
    queryset = Mod.objects.filter(approved=True)
    serializer_class = ModSerializer
    lookup_field = "uuid"


class ModCreateAPIView(generics.CreateAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer


class ModUpdateAPIView(generics.UpdateAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer
    lookup_field = "uuid"


class ModDeleteAPIView(generics.DestroyAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer
    lookup_field = "uuid"


class TagListAPIView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ModSearchByCategoryAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        category_id = self.kwargs["category_id"]
        return Mod.objects.filter(category__id=category_id, approved=True)


class ModSearchByTagAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        tag_ids = self.request.query_params.getlist("tag_ids")
        queryset = Mod.objects.filter(approved=True)
        for tag_id in tag_ids:
            queryset = queryset.filter(tags__id=tag_id)
        return queryset


class ModSearchByTitleAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        title = self.kwargs["title"]
        return Mod.objects.filter(title__icontains=title, approved=True)


class ModSearchByUserAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        return Mod.objects.filter(user__id=user_id, approved=True)


class ModSearchByRaceAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        race_ids = self.request.query_params.getlist("race_ids")
        queryset = Mod.objects.filter(approved=True)
        for race_id in race_ids:
            queryset = queryset.filter(modcompatibility__race__id=race_id)
        return queryset


class ModSearchByGenderAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        gender_ids = self.request.query_params.getlist("gender_ids")
        queryset = Mod.objects.filter(approved=True)
        if gender_ids:
            queryset = queryset.filter(modcompatibility__gender__id__in=gender_ids)
        return queryset


class RaceListAPIView(generics.ListAPIView):
    queryset = Race.objects.all()
    serializer_class = RaceSerializer


class GenderListAPIView(generics.ListAPIView):
    queryset = Gender.objects.all()
    serializer_class = GenderSerializer
