from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=40, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    requires_race = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True, db_index=True)


class Race(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)


class Gender(models.Model):
    name = models.CharField(max_length=10, unique=True, db_index=True)

    def __str__(self):
        return self.name


class ModCompatibility(models.Model):
    mod = models.ForeignKey("Mod", on_delete=models.CASCADE, db_index=True)
    race = models.ForeignKey(Race, on_delete=models.CASCADE, db_index=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, blank=True, null=True, db_index=True)

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
    file_size = models.PositiveBigIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    downloads = models.PositiveIntegerField(default=0, db_index=True)
    categories = models.ManyToManyField(Category, related_name="mods", db_index=True)
    tags = models.ManyToManyField(Tag, related_name="mods", blank=True, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)
    thumbnail = models.URLField(blank=True, null=True)

    def clean(self):
        if not isinstance(self.file_size, int):
            raise ValueError("File size must be an integer.")
        if not isinstance(self.version, str):
            raise ValueError("Version must be a string with a maximum of 20 characters.")
        if self.file_size <= 0:
            raise ValueError("File size must be a positive integer.")
        if self.file_size > 1073741824:
            raise ValueError("File size must be less than 1GB.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.categories.filter(requires_race=True).exists():
            if not ModCompatibility.objects.filter(mod=self, race__isnull=False).exists():
                raise ValueError("One or more compatible races must be selected.")
            if not ModCompatibility.objects.filter(mod=self, gender__isnull=False).exists():
                raise ValueError("One or more compatible genders must be selected.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ModImage(models.Model):
    mod = models.ForeignKey(Mod, on_delete=models.CASCADE, db_index=True)
    image = models.ImageField(upload_to="mod_images/")
    is_thumbnail = models.BooleanField(default=False, db_index=True)

    def save(self, *args, **kwargs):
        if self.is_thumbnail:
            # Unset all other thumbnails
            ModImage.objects.filter(mod=self.mod, is_thumbnail=True).update(is_thumbnail=False)
            self.mod.thumbnail = self.image.url
            self.mod.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.image.url
