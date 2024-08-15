import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .models import Category, Gender, Mod, ModCompatibility, ModImage, Race

User = get_user_model()


class ModModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="testuser", email=f"{uuid.uuid4()}@example.com")
        self.category = Category.objects.create(name="Test Category")
        self.mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        self.mod.categories.add(self.category)

    def test_unique_email_constraint(self):
        user1 = User.objects.create(username="user1", email=f"{uuid.uuid4()}@example.com")
        with self.assertRaises(IntegrityError):
            User.objects.create(username="user2", email=user1.email)

    def test_mod_saves_with_thumbnail(self):
        image = ModImage.objects.create(mod=self.mod, image="path/to/image.jpg", is_thumbnail=True)
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.thumbnail, image.image.url)

    def test_only_one_thumbnail_per_mod(self):
        image1 = ModImage.objects.create(mod=self.mod, image="path/to/image1.jpg", is_thumbnail=True)
        image2 = ModImage.objects.create(mod=self.mod, image="path/to/image2.jpg", is_thumbnail=True)
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.thumbnail, image2.image.url)
        self.assertFalse(ModImage.objects.get(id=image1.id).is_thumbnail)

    def test_mod_without_thumbnail(self):
        ModImage.objects.create(mod=self.mod, image="path/to/image.jpg", is_thumbnail=False)
        self.mod.refresh_from_db()
        self.assertIsNone(self.mod.thumbnail)

    def test_mod_with_multiple_images(self):
        image1 = ModImage.objects.create(mod=self.mod, image="path/to/image1.jpg", is_thumbnail=True)
        image2 = ModImage.objects.create(mod=self.mod, image="path/to/image2.jpg", is_thumbnail=False)
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.modimage_set.count(), 2)
        self.assertEqual(self.mod.thumbnail, image1.image.url)
        self.assertIn(image2, self.mod.modimage_set.all())

    def test_mod_with_no_images(self):
        self.mod.modimage_set.all().delete()
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.modimage_set.count(), 0)
        self.assertIsNone(self.mod.thumbnail)

    def test_mod_saves_with_single_category(self):
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.categories.first(), self.category)

    def test_mod_saves_with_multiple_categories(self):
        category2 = Category.objects.create(name="Another Category")
        self.mod.categories.add(category2)
        self.mod.refresh_from_db()
        self.assertIn(category2, self.mod.categories.all())

    def test_mod_without_categories(self):
        self.mod.categories.clear()
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.categories.count(), 0)

    def test_mod_with_invalid_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=2,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size="invalid_size",
                user=User.objects.create(username="anotheruser", email=f"{uuid.uuid4()}@example.com"),
                approved=True,
            )

    def test_mod_with_negative_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=2,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=-1,
                user=self.user,
                approved=True,
            )

    def test_mod_with_too_large_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=2,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=1000000000000,
                user=self.user,
                approved=True,
            )

    def test_mod_with_512mb_file_size(self):
        mod = Mod.objects.create(
            id=2,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=536870912,
            user=self.user,
            approved=True,
        )
        self.assertEqual(mod.file_size, 536870912)

    def test_mod_with_1gb_file_size(self):
        file_size = 1073741824
        mod = Mod.objects.create(
            id=2,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=file_size,
            user=self.user,
            approved=True,
        )
        self.assertEqual(mod.file_size, file_size)

    def test_mod_with_duplicate_title(self):
        Mod.objects.create(
            id=3,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=User.objects.create(username="anotheruser", email=f"{uuid.uuid4()}@example.com"),
            approved=True,
        )
        self.assertEqual(Mod.objects.filter(title="Test Mod").count(), 2)

    def test_mod_with_duplicate_user(self):
        Mod.objects.create(
            id=3,
            title="Another Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        self.assertEqual(Mod.objects.filter(user=self.user).count(), 2)

    def test_mod_with_invalid_version(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=3,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version=1,
                file_size=1000000,
                user=self.user,
                approved=True,
            )

    def test_mod_with_zero_file_size(self):
        zero_file_size = 0
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=4,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=zero_file_size,
                user=self.user,
                approved=True,
            )

    def test_mod_with_max_file_size(self):
        max_file_size = 9223372036854775807
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=5,
                title="Valid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=max_file_size,
                user=self.user,
                approved=True,
            )

    def test_mod_requires_race_without_compatible_race(self):
        # Set requires_race to True and save the category
        self.category.requires_race = True
        self.category.save()

        # Ensure the category is associated with the mod
        self.mod.categories.add(self.category)

        # Ensure no ModCompatibility exists for the mod (i.e., no race is set)
        ModCompatibility.objects.filter(mod=self.mod).delete()

        # Attempt to save the mod and expect a ValueError
        with self.assertRaises(ValueError):
            self.mod.save()

    def test_mod_requires_race_with_compatible_race(self):
        race = Race.objects.create(name="Test Race")
        ModCompatibility.objects.create(mod=self.mod, race=race)
        self.mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=self.mod, race=race).exists())

    def test_mod_requires_gender_without_compatible_gender(self):
        self.category.requires_gender = True
        self.category.save()

        self.mod.categories.add(self.category)

        ModCompatibility.objects.filter(mod=self.mod).delete()

        with self.assertRaises(ValueError):
            self.mod.save()

    def test_mod_requires_gender_with_compatible_gender(self):
        gender = Gender.objects.create(name="Test Gender")
        race = Race.objects.create(name="Test Race")
        ModCompatibility.objects.create(mod=self.mod, gender=gender, race=race)
        self.mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=self.mod, gender=gender).exists())
