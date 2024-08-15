from rest_framework import generics

from .models import Mod
from .serializers import ModSerializer


class ModListAPIView(generics.ListAPIView):
    queryset = Mod.objects.filter(approved=True)
    serializer_class = ModSerializer


class ModDetailAPIView(generics.RetrieveAPIView):
    queryset = Mod.objects.filter(approved=True)
    serializer_class = ModSerializer


class ModSearchByCategoryAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        category_id = self.kwargs["category_id"]
        return Mod.objects.filter(categories__id=category_id, approved=True)


class ModSearchByTagAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        tag_id = self.kwargs["tag_id"]
        return Mod.objects.filter(tags__id=tag_id, approved=True)


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
        race_id = self.kwargs["race_id"]
        return Mod.objects.filter(modcompatibility__race__id=race_id, approved=True)


class ModSearchByGenderAPIView(generics.ListAPIView):
    serializer_class = ModSerializer

    def get_queryset(self):
        gender_id = self.kwargs["gender_id"]
        return Mod.objects.filter(modcompatibility__gender__id=gender_id, approved=True)
