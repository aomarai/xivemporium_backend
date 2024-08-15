from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    requires_race = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)


class Race(models.Model):
    name = models.CharField(max_length=120, unique=True)


class Gender(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class ModCompatibility(models.Model):
    mod = models.ForeignKey("Mod", on_delete=models.CASCADE)
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.mod.title} - {self.race.name} - {self.gender.name if self.gender else None}"


class Mod(models.Model):
    title = models.CharField(max_length=120, db_index=True)
    short_desc = models.TextField(max_length=200)
    description = models.TextField(max_length=1000)
    version = models.CharField(max_length=20, default="1.0.0")
    upload_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    file = models.FileField(upload_to="mods/")
    file_size = models.BigIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    downloads = models.IntegerField(default=0)
    categories = models.ManyToManyField(Category, related_name="mods", db_index=True)
    tags = models.ManyToManyField(Tag, related_name="mods", blank=True, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)
    thumbnail = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.categories.filter(requires_race=True).exists():
            if not ModCompatibility.objects.filter(mod=self, race__isnull=False).exists():
                raise ValueError("This mod requires one or more compatible races to be selected.")
            if not ModCompatibility.objects.filter(mod=self, gender__isnull=False).exists():
                raise ValueError("This mod requires one or more compatible genders to be selected.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ModImage(models.Model):
    mod = models.ForeignKey(Mod, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="mod_images/")
    is_thumbnail = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_thumbnail:
            # Unset all other thumbnails
            ModImage.objects.filter(mod=self.mod, is_thumbnail=True).update(is_thumbnail=False)
            self.mod.thumbnail = self.image.url
            self.mod.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.image.url
