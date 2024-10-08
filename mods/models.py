from uuid import uuid4
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator,
    URLValidator,
    EmailValidator,
)
from django.core.exceptions import ValidationError


_USER_UPLOADED_MODS_PATH = "user_uploads"


def get_image_upload_path(instance, filename):
    return f"{_USER_UPLOADED_MODS_PATH}/{instance.mod.uuid}/images/{filename}"


def get_mod_upload_path(instance, filename):
    return f"{_USER_UPLOADED_MODS_PATH}/{instance.uuid}/files/{filename}"


class User(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("moderator", "Moderator"),
        ("admin", "Admin"),
    ]

    username = models.CharField(
        max_length=40, unique=True, db_index=True, validators=[MinLengthValidator(2), MaxLengthValidator(40)]
    )
    email = models.EmailField(unique=True, db_index=True, validators=[EmailValidator()])
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user", db_index=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=20, unique=True, db_index=True, validators=[MinLengthValidator(2), MaxLengthValidator(20)]
    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Race(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True, editable=False)

    def __str__(self):
        return self.name


class Gender(models.Model):
    name = models.CharField(max_length=10, unique=True, db_index=True, editable=False)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        db_index=True,
        editable=False,
        validators=[MinLengthValidator(2), MaxLengthValidator(120)],
    )
    requires_race = models.BooleanField(default=False, db_index=True)
    requires_gender = models.BooleanField(default=False, db_index=True)

    def clean(self):
        self.full_clean()

    def __str__(self):
        return self.name


class ModCompatibility(models.Model):
    mod = models.ForeignKey("Mod", on_delete=models.CASCADE, db_index=True)
    race = models.ForeignKey(Race, on_delete=models.CASCADE, db_index=True)
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.mod.title} - {self.race.name} - {self.gender.name if self.gender else None}"


class Mod(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True, db_index=True)
    title = models.CharField(max_length=120, db_index=True, validators=[MinLengthValidator(5), MaxLengthValidator(120)])
    short_desc = models.TextField(
        max_length=200, validators=[MinLengthValidator(0), MaxLengthValidator(200)], db_index=True
    )
    description = models.TextField(max_length=1000, validators=[MinLengthValidator(0), MaxLengthValidator(1000)])
    version = models.CharField(
        max_length=25, default="1.0.0", validators=[MinLengthValidator(1), MaxLengthValidator(25)]
    )
    upload_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    file = models.FileField(upload_to=get_mod_upload_path, db_index=True)
    file_size = models.PositiveBigIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1073741824)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    downloads = models.PositiveBigIntegerField(default=0, db_index=True, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_index=True)
    tags = models.ManyToManyField(Tag, related_name="mods", blank=True, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)
    thumbnail = models.URLField(blank=True, null=True, validators=[URLValidator()], db_index=True)

    def save(self, *args, **kwargs):
        self.full_clean()  # Perform model field validations

        # Perform custom validations
        if not self.category:
            raise ValidationError("A category must be selected.")
        if self.category.requires_race and not ModCompatibility.objects.filter(mod=self, race__isnull=False).exists():
            raise ValidationError("One or more compatible races must be selected.")
        if (
            self.category.requires_gender
            and not ModCompatibility.objects.filter(mod=self, gender__isnull=False).exists()
        ):
            raise ValidationError("One or more compatible genders must be selected.")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ModImage(models.Model):
    ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]
    MAXIMUM_FILE_SIZE = 5242880  # 5MB

    mod = models.ForeignKey(Mod, on_delete=models.CASCADE, db_index=True)
    image = models.ImageField(
        upload_to=get_image_upload_path,
        db_index=True,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)],
    )
    is_thumbnail = models.BooleanField(default=False, db_index=True)

    def clean(self):
        """Validate the ModImage before saving."""
        if self.image.size > self.MAXIMUM_FILE_SIZE:
            raise ValidationError("Image file size must be less than 5MB.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Perform model field validations

        # If this is the thumbnail, ensure it's the only one
        if self.is_thumbnail:
            ModImage.objects.filter(mod=self.mod, is_thumbnail=True).exclude(id=self.id).update(is_thumbnail=False)
            self.mod.thumbnail = self.image.url
            self.mod.save(update_fields=["thumbnail"])
        else:
            # If this is the only image, make it the thumbnail
            if not ModImage.objects.filter(mod=self.mod).exclude(id=self.id).exists():
                self.is_thumbnail = True
                self.mod.thumbnail = self.image.url
                self.mod.save(update_fields=["thumbnail"])

        super().save(*args, **kwargs)

    def __str__(self):
        return self.image.url


class Comment(models.Model):
    mod = models.ForeignKey(Mod, related_name="comments", on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    text = models.TextField(
        max_length=500, validators=[MinLengthValidator(1), MaxLengthValidator(500)], blank=False, null=False
    )
    comment_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.text:
            raise ValidationError("Comment text must not be empty.")
        if not isinstance(self.text, str):
            raise ValidationError("Comment must be a string.")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.comment_date}"


class Download(models.Model):
    mod = models.ForeignKey(Mod, related_name="mod_downloads", on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    download_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        self.mod.downloads += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.download_date}"


class Rating(models.Model):
    mod = models.ForeignKey(Mod, related_name="ratings", on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.rating_date}"
