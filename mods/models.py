from django.db import models


class User(models.Model):
    username = models.CharField(max_length=120)
    email = models.EmailField()
    date_joined = models.DateTimeField(auto_now_add=True)
    password_hash = models.CharField(max_length=120)
    password_salt = models.CharField(max_length=120)

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


class Mod(models.Model):
    title = models.CharField(max_length=120)
    short_desc = models.TextField(max_length=200)
    description = models.TextField(max_length=1000)
    version = models.CharField(max_length=20, default="1.0.0")
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="mods/")
    file_size = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    downloads = models.IntegerField(default=0)
    categories = models.ManyToManyField(Category, related_name="mods")
    races = models.ManyToManyField(Race, related_name="mods", blank=True)
    tags = models.ManyToManyField(Tag, related_name="mods", blank=True)

    def save(self, *args, **kwargs):
        if self.categories.filter(requires_race=True).exists() and not self.races.exists():
            raise ValueError("This mod requires one or more compatible races to be selected.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ModImage(models.Model):
    mod = models.ForeignKey(Mod, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="mod_images/")


def __str__(self):
    return self.title
