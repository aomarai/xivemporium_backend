import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .models import Category, Gender, Mod, ModCompatibility, ModImage, Race

User = get_user_model()


class ModModelTests(TestCase):

    def setUp(self):
        # Common setup for each test, if needed
        self.user = User.objects.create(username="testuser", email=f"{uuid.uuid4()}@example.com")

    def test_unique_email_constraint(self):
        user1 = User.objects.create(username="user1", email=f"{uuid.uuid4()}@example.com")
        with self.assertRaises(IntegrityError):
            User.objects.create(username="user2", email=user1.email)

    def test_mod_saves_with_thumbnail(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)  # Now add categories
        image = ModImage.objects.create(mod=mod, image="path/to/image.jpg", is_thumbnail=True)
        mod.refresh_from_db()
        self.assertEqual(mod.thumbnail, image.image.url)

    def test_only_one_thumbnail_per_mod(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)  # Now add categories
        image1 = ModImage.objects.create(mod=mod, image="path/to/image1.jpg", is_thumbnail=True)
        image2 = ModImage.objects.create(mod=mod, image="path/to/image2.jpg", is_thumbnail=True)
        mod.refresh_from_db()
        self.assertEqual(mod.thumbnail, image2.image.url)
        self.assertFalse(ModImage.objects.get(id=image1.id).is_thumbnail)

    def test_mod_without_thumbnail(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)  # Now add categories
        ModImage.objects.create(mod=mod, image="path/to/image.jpg", is_thumbnail=False)
        mod.refresh_from_db()
        self.assertIsNone(mod.thumbnail)

    def test_mod_with_multiple_images(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)  # Now add categories
        image1 = ModImage.objects.create(mod=mod, image="path/to/image1.jpg", is_thumbnail=True)
        image2 = ModImage.objects.create(mod=mod, image="path/to/image2.jpg", is_thumbnail=False)
        mod.refresh_from_db()
        self.assertEqual(mod.modimage_set.count(), 2)
        self.assertEqual(mod.thumbnail, image1.image.url)
        self.assertIn(image2, mod.modimage_set.all())

    def test_mod_with_no_images(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)  # Now add categories
        mod.modimage_set.all().delete()
        mod.refresh_from_db()
        self.assertEqual(mod.modimage_set.count(), 0)
        self.assertIsNone(mod.thumbnail)

    def test_mod_saves_with_single_category(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)
        mod.refresh_from_db()
        self.assertEqual(mod.categories.first(), category)

    def test_mod_saves_with_multiple_categories(self):
        category1 = Category.objects.create(name="Test Category 1")
        category2 = Category.objects.create(name="Test Category 2")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category1, category2)
        mod.refresh_from_db()
        self.assertIn(category2, mod.categories.all())

    def test_mod_without_categories(self):
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.clear()
        mod.refresh_from_db()
        self.assertEqual(mod.categories.count(), 0)

    def test_mod_with_invalid_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=1,
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
                id=1,
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
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=1000000000000,
                user=self.user,
                approved=True,
            )

    def test_mod_with_512mb_file_size(self):
        file_size = 536870912  # 512 MB in bytes
        mod = Mod.objects.create(
            id=1,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=file_size,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        self.assertEqual(mod.file_size, file_size)

    def test_mod_with_1gb_file_size(self):
        file_size = 1073741824  # 1 GB in bytes
        mod = Mod.objects.create(
            id=1,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=file_size,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        self.assertEqual(mod.file_size, file_size)

    def test_mod_with_duplicate_title(self):
        test_title = "Test Mod"
        Mod.objects.create(
            id=1,
            title=test_title,
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=User.objects.create(username="anotheruser", email=f"{uuid.uuid4()}@example.com"),
            approved=True,
        )

        # Create another mod with the same title
        Mod.objects.create(
            id=2,
            title=test_title,
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=User.objects.create(username="yetanotheruser", email=f"{uuid.uuid4()}@example.com"),
            approved=True,
        )

        self.assertEqual(Mod.objects.filter(title="Test Mod").count(), 2)

    def test_mod_with_duplicate_user(self):
        Mod.objects.create(
            id=1,
            title="Another Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )

        # Create another mod with the same user
        Mod.objects.create(
            id=2,
            title="Yet Another Mod",
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
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version=1,  # Invalid version format
                file_size=1000000,
                user=self.user,
                approved=True,
            )

    def test_mod_with_zero_file_size(self):
        zero_file_size = 0
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=zero_file_size,
                user=self.user,
                approved=True,
            )

    def test_mod_with_max_file_size(self):
        max_file_size = 9223372036854775807  # Max value for a signed 64-bit integer
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=1,
                title="Valid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=max_file_size,
                user=self.user,
                approved=True,
            )

    def test_mod_requires_race_without_compatible_race(self):
        category = Category.objects.create(name="Test Category", requires_race=True)
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)
        ModCompatibility.objects.filter(mod=mod).delete()

        with self.assertRaises(ValueError):
            mod.save()

    def test_mod_requires_race_with_compatible_race(self):
        category = Category.objects.create(name="Test Category", requires_race=True)
        race = Race.objects.create(name="Test Race")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)
        ModCompatibility.objects.create(mod=mod, race=race)
        mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=mod, race=race).exists())

    def test_mod_requires_gender_without_compatible_gender(self):
        category = Category.objects.create(name="Test Category", requires_gender=True)
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)
        ModCompatibility.objects.filter(mod=mod).delete()

        with self.assertRaises(ValueError):
            mod.save()

    def test_mod_requires_gender_with_compatible_gender(self):
        category = Category.objects.create(name="Test Category", requires_gender=True)
        gender = Gender.objects.create(name="Test Gender")
        race = Race.objects.create(name="Test Race")
        mod = Mod.objects.create(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.categories.add(category)
        ModCompatibility.objects.create(mod=mod, gender=gender, race=race)
        mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=mod, gender=gender).exists())
