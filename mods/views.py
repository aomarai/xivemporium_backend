from rest_framework import generics, status, serializers
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import Mod, Race, Gender, Tag
from .serializers import ModSerializer, RaceSerializer, GenderSerializer, TagSerializer, UserRegistrationSerializer
from .permissions import IsModeratorOrAdmin, IsModeratorOrAdminOrOwner


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
    permission_classes = [IsAuthenticated]


class ModUpdateAPIView(generics.UpdateAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer
    lookup_field = "uuid"
    permission_classes = [IsAuthenticated, IsModeratorOrAdminOrOwner]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)  # Allow partial updates
        instance = self.get_object()

        # Populate any missing data in the request with the current instance's data
        data = request.data.copy()
        for field in self.serializer_class.Meta.fields:
            if field not in data and hasattr(instance, field):
                data[field] = getattr(instance, field)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class ModDeleteAPIView(generics.DestroyAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer
    lookup_field = "uuid"
    permission_classes = [IsAuthenticated, IsModeratorOrAdminOrOwner]


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


class UserRegistrationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModApprovalAPIView(UpdateAPIView):
    queryset = Mod.objects.all()
    serializer_class = ModSerializer
    permission_classes = [IsModeratorOrAdmin]
    lookup_field = "uuid"

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        data = request.data.copy()

        if "approved" not in data:
            raise serializers.ValidationError({"approved": "This field is required."})

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
