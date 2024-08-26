import io
import os
import random
import uuid
import time
import shutil
from urllib.parse import urlparse
from os.path import basename
from .models import USER_UPLOADED_MODS_PATH, Comment

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Gender, Mod, ModCompatibility, ModImage, Race, Tag

User = get_user_model()


class ModModelTests(TestCase):

    def setUp(self):
        # Common setup for each test, if needed
        self.user = User.objects.create(username="testuser", email=f"{uuid.uuid4()}@example.com")
        self.category = Category.objects.create(name="Initial Category")

    def tearDown(self):
        # Ensure cleanup runs after the transaction is complete
        def cleanup():
            # Clean up any images created during the tests
            for mod_image in ModImage.objects.all():
                if mod_image.image and os.path.isfile(mod_image.image.path):
                    os.remove(mod_image.image.path)
                mod_image.delete()

            # Clean up all mods
            Mod.objects.all().delete()

            # Clean up all categories
            Category.objects.all().delete()

            # Clean up all users
            User.objects.all().delete()

        transaction.on_commit(cleanup)

        # Delete the uploaded user mods directory if it exists
        shutil.rmtree(USER_UPLOADED_MODS_PATH, ignore_errors=True)

    def test_unique_email_constraint(self):
        user1 = User.objects.create(username="user1", email=f"{uuid.uuid4()}@example.com")
        with self.assertRaises(IntegrityError):
            User.objects.create(username="user2", email=user1.email)

    def test_mod_saves_with_thumbnail(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID
        image = SimpleUploadedFile("image.jpg", b"file_content", content_type="image/jpeg")
        mod_image = ModImage.objects.create(mod=mod, image=image, is_thumbnail=True)
        mod.refresh_from_db()

        # Parse the thumbnail URL and the image URL
        thumbnail_url = urlparse(mod.thumbnail)

        # Extract the file names from the URLs
        thumbnail_file_name = basename(thumbnail_url.path)

        # Check that the thumbnail file name matches the image file name
        self.assertTrue(ModImage.objects.get(id=mod_image.id).is_thumbnail)
        self.assertTrue(thumbnail_file_name.startswith("image"))

    def test_only_one_thumbnail_per_mod(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID

        # Simulate image uploads
        image1 = SimpleUploadedFile("image1.jpg", b"file_content", content_type="image/jpeg")
        image2 = SimpleUploadedFile("image2.jpg", b"file_content", content_type="image/jpeg")

        mod_image1 = ModImage.objects.create(mod=mod, image=image1, is_thumbnail=True)
        ModImage.objects.create(mod=mod, image=image2, is_thumbnail=True)

        mod.refresh_from_db()

        # Parse the thumbnail URL
        thumbnail_url = urlparse(mod.thumbnail)

        # Extract the file name from the URL
        thumbnail_file_name = thumbnail_url.path.split("/")[-1]
        expected_file_name_prefix = "image2"

        # Check that the thumbnail file name starts with the expected prefix
        self.assertTrue(thumbnail_file_name.startswith(expected_file_name_prefix))
        self.assertFalse(ModImage.objects.get(id=mod_image1.id).is_thumbnail)

    def test_mod_without_thumbnail(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID
        image = SimpleUploadedFile("image.jpg", b"file_content", content_type="image/jpeg")
        ModImage.objects.create(mod=mod, image=image, is_thumbnail=False)
        mod.refresh_from_db()
        self.assertIsNotNone(mod.thumbnail)

    def test_mod_with_multiple_images(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID
        image1 = SimpleUploadedFile("image1.jpg", b"file_content", content_type="image/jpeg")
        image2 = SimpleUploadedFile("image2.jpg", b"file_content", content_type="image/jpeg")
        image3 = SimpleUploadedFile("image3.jpg", b"file_content", content_type="image/jpeg")

        mod_image1 = ModImage.objects.create(mod=mod, image=image1, is_thumbnail=True)
        ModImage.objects.create(mod=mod, image=image2, is_thumbnail=False)
        ModImage.objects.create(mod=mod, image=image3, is_thumbnail=False)

        # Parse the thumbnail URL
        thumbnail_url = urlparse(mod.thumbnail)

        # Extract the file name from the URL
        thumbnail_file_name = thumbnail_url.path.split("/")[-1]
        expected_file_name_prefix = "image1"

        mod.refresh_from_db()

        # Check that the thumbnail file name starts with the expected prefix
        self.assertTrue(thumbnail_file_name.startswith(expected_file_name_prefix))
        self.assertTrue(ModImage.objects.get(id=mod_image1.id).is_thumbnail)
        self.assertEqual(mod.modimage_set.count(), 3)

    def test_mod_with_no_images(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.modimage_set.all().delete()
        mod.refresh_from_db()
        self.assertEqual(mod.modimage_set.count(), 0)
        self.assertIsNone(mod.thumbnail)

    def test_mod_saves_with_single_category(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()  # Save mod to ensure it has an ID
        self.assertEqual(mod.category, category)

    def test_mod_without_categories(self):
        with self.assertRaises(ValidationError):
            mod = Mod.objects.create(
                id=1,
                title="Test Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=1000000,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
            )
            mod.save()

    def test_mod_with_string_file_size(self):
        with self.assertRaises(ValidationError):
            mod = Mod(
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size="invalid_size",
                user=User.objects.create(username="anotheruser", email=f"{uuid.uuid4()}@example.com"),
                approved=True,
                file="path/to/file.zip",
                category=self.category,
            )
            mod.save()

    def test_mod_with_negative_file_size(self):
        with self.assertRaises(ValidationError):
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
        with self.assertRaises(ValidationError):
            mod = Mod(
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=1000000000000,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
            )
            mod.save()

    def test_mod_with_512mb_file_size(self):
        file_size = 536870912  # 512 MB in bytes
        mod = Mod(
            id=1,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=file_size,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod to ensure it has an ID
        self.assertEqual(mod.file_size, file_size)

    def test_mod_with_1gb_file_size(self):
        file_size = 1073741824  # 1 GB in bytes
        mod = Mod(
            id=1,
            title="Valid Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=file_size,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod to ensure it has an ID
        self.assertEqual(mod.file_size, file_size)

    def test_mod_with_duplicate_title(self):
        test_title = "Test Mod"
        mod1 = Mod(
            id=1,
            title=test_title,
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=User.objects.create(username="anotheruser", email=f"{uuid.uuid4()}@example.com"),
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod1.save()

        # Create another mod with the same title
        mod2 = Mod(
            id=2,
            title=test_title,
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=User.objects.create(username="yetanotheruser", email=f"{uuid.uuid4()}@example.com"),
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod2.save()

        self.assertEqual(Mod.objects.filter(title="Test Mod").count(), 2)

    def test_mod_with_empty_title(self):
        with self.assertRaises(ValidationError):
            Mod.objects.create(
                id=1,
                title="",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=1000000,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
                category=self.category,
            )

    def test_mod_with_duplicate_user(self):
        mod1 = Mod(
            id=1,
            title="Another Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod1.save()

        # Create another mod with the same user
        mod2 = Mod(
            id=2,
            title="Yet Another Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod2.save()

        self.assertEqual(Mod.objects.filter(user=self.user).count(), 2)

    def test_mod_with_zero_file_size(self):
        zero_file_size = 0
        with self.assertRaises(ValidationError):
            mod = Mod(
                id=1,
                title="Invalid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=zero_file_size,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
                category=self.category,
            )
            mod.full_clean()
            mod.save()

    def test_mod_with_max_file_size(self):
        max_file_size = 9223372036854775807  # Max value for a signed 64-bit integer
        with self.assertRaises(ValidationError):
            mod = Mod(
                id=1,
                title="Valid Mod",
                short_desc="Short description",
                description="Long description",
                version="1.0.0",
                file_size=max_file_size,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
                category=self.category,
            )
            mod.full_clean()
            mod.save()

    def test_mod_requires_race_without_compatible_race(self):
        # Create a category that requires a race
        category_requires_race = Category.objects.create(name="Test Category", requires_race=True)

        # Create and save the Mod with the race-required category
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod with the valid category

        # Now replace the valid category with the one that requires a race
        mod.category = category_requires_race

        # Ensure no ModCompatibility entries exist for this mod (simulate missing races)
        ModCompatibility.objects.filter(mod=mod).delete()

        # Attempt to save the Mod and expect a ValidationError due to the missing race
        with self.assertRaises(ValidationError) as context:
            mod.save()

        # Optionally, you can check the message of the ValidationError if needed
        self.assertIn("compatible races", str(context.exception))

    def test_mod_requires_race_with_compatible_race(self):
        race = Race.objects.create(name="Test Race")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod to ensure it has an ID
        ModCompatibility.objects.create(mod=mod, race=race)
        mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=mod, race=race).exists())

    def test_mod_requires_gender_without_compatible_gender(self):
        category = Category.objects.create(name="Test Category", requires_gender=True)
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.category = category
        ModCompatibility.objects.filter(mod=mod).delete()

        with self.assertRaises(ValidationError):
            mod.save()

    def test_mod_requires_gender_with_compatible_gender(self):
        category = Category.objects.create(name="Test Category", requires_gender=True)
        gender = Gender.objects.create(name="Test Gender")
        race = Race.objects.create(name="Test Race")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()  # Save mod to ensure it has an ID
        mod.category = category
        ModCompatibility.objects.create(mod=mod, gender=gender, race=race)
        mod.save()
        self.assertTrue(ModCompatibility.objects.filter(mod=mod, gender=gender).exists())

    def test_mod_description_length(self):
        category = Category.objects.create(name="Test Category")
        valid_description = "a" * 1000
        invalid_description = "a" * 1001

        # Test with valid description length
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description=valid_description,
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()
        self.assertEqual(mod.description, valid_description)

        # Test with invalid description length
        with self.assertRaises(ValidationError):
            mod2 = Mod(
                id=2,
                title="Invalid Mod",
                short_desc="Short description",
                description=invalid_description,
                version="1.0.0",
                file_size=1000000,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
                category=category,
            )
            mod2.full_clean()  # This will trigger the validation
            mod2.save()

    def test_mod_short_desc_length(self):
        category = Category.objects.create(name="Test Category")
        valid_short_desc = "a" * 200
        invalid_short_desc = "a" * 201

        # Test with valid short description length
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc=valid_short_desc,
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()
        self.assertEqual(mod.short_desc, valid_short_desc)

        # Test with invalid short description length
        with self.assertRaises(ValidationError):
            mod2 = Mod(
                id=2,
                title="Invalid Mod",
                short_desc=invalid_short_desc,
                description="Long description",
                version="1.0.0",
                file_size=1000000,
                user=self.user,
                approved=True,
                file="path/to/file.zip",
                category=category,
            )
            mod2.full_clean()  # This will trigger the validation
            mod2.save()

    def test_mod_upload_date(self):
        Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )
        mod.save()

        self.assertIsNotNone(mod.upload_date)
        self.assertIsNotNone(mod.updated_date)
        self.assertLessEqual(mod.upload_date, mod.updated_date)

    def test_mod_updated_date(self):
        category = Category.objects.create(name="Test Category")
        mod = Mod(
            id=1,
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=category,
        )
        mod.save()

        # Store the initial upload and update dates
        initial_upload_date = mod.upload_date
        initial_updated_date = mod.updated_date

        # Introduce a short delay to ensure updated_date is different
        time.sleep(1)

        # Update the mod and save again
        mod.title = "Updated Mod"
        mod.save()

        # Refresh from the database
        mod.refresh_from_db()

        self.assertIsNotNone(mod.updated_date)
        self.assertEqual(mod.upload_date, initial_upload_date)
        self.assertGreater(mod.updated_date, initial_updated_date)


class ModAPITests(APITestCase):

    def setUp(self):
        category_two = Category.objects.create(name="Another Category")

        file_content = io.BytesIO(b"file_content" * 1024)
        self.file = SimpleUploadedFile("file.zip", file_content.read(), content_type="application/zip")
        self.user = User.objects.create(username="testuser", email=f"{uuid.uuid4()}@example.com")
        self.category = Category.objects.create(name="Test Category")
        self.category_two = category_two  # Save the second category
        self.tag = Tag.objects.create(name="Test Tag")
        self.race = Race.objects.create(name="Test Race")
        self.gender = Gender.objects.create(name="Test Gender")
        self.mod = Mod(
            id=random.randint(1, 1000),
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file=self.file,
            file_size=self.file.size,
            user=self.user,
            approved=True,
            category=self.category,  # Assign category directly
        )
        self.mod.save()
        self.mod.tags.add(self.tag)
        ModCompatibility.objects.create(mod=self.mod, race=self.race, gender=self.gender)

    def tearDown(self):
        Mod.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete

    def test_mod_list_api_view_returns_approved_mods(self):
        url = reverse("list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_detail_api_view_returns_mod_details(self):
        url = reverse("detail", kwargs={"uuid": self.mod.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.mod.title)

    def test_mod_search_by_category_api_view_returns_mods_in_category(self):
        url = reverse("search-by-category", kwargs={"category_id": self.category.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_search_by_tag_api_view_returns_mods_with_tags(self):
        url = reverse("search-by-tag")
        response = self.client.get(url, {"tag_ids": [self.tag.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_search_by_title_api_view_returns_mods_with_title(self):
        url = reverse("search-by-title", kwargs={"title": "Test"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_search_by_user_api_view_returns_mods_by_user(self):
        url = reverse("search-by-user", kwargs={"user_id": self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_search_by_race_api_view_returns_mods_with_race(self):
        url = reverse("search-by-race")
        response = self.client.get(url, {"race_ids": [self.race.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_search_by_gender_api_view_returns_mods_with_gender(self):
        url = reverse("search-by-gender")
        response = self.client.get(url, {"gender_ids": [self.gender.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.mod.title)

    def test_mod_create_api_view_creates_mod(self):
        url = reverse("create")

        data = {
            "title": "New Mod",
            "short_desc": "New short description",
            "description": "New long description",
            "version": "1.0.0",
            "file": self.file,
            "file_size": self.file.size,
            "user": self.user.id,
            "approved": True,
            "category": self.category_two.id,  # Use the ID of the second category
            "tags": [self.tag.id],
        }

        # Reset the file pointer to ensure it's read correctly
        self.file.seek(0)

        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mod.objects.count(), 2)
        self.assertEqual(Mod.objects.get(id=response.data["id"]).title, "New Mod")

    def test_mod_create_api_view_fails_with_invalid_data(self):
        url = reverse("create")
        data = {
            "title": "",
            "short_desc": "New short description",
            "description": "New long description",
            "version": "1.0.0",
            "file": SimpleUploadedFile("file.zip", b"file_content", content_type="application/zip"),
            "file_size": self.file.size,
            "user": self.user.id,
            "approved": True,
            "categories": [self.category.id],
            "tags": [self.tag.id],
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Mod.objects.count(), 1)

    def test_mod_list_api_view_returns_empty_list_when_no_mods(self):
        Mod.objects.all().delete()
        url = reverse("list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_mod_detail_api_view_returns_404_for_nonexistent_mod(self):
        url = reverse("detail", kwargs={"uuid": uuid.uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CommentModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="testuser", email=f"{uuid.uuid4()}@example.com")
        self.category = Category.objects.create(name="Test Category")
        self.mod = Mod.objects.create(
            title="Test Mod",
            short_desc="Short description",
            description="Long description",
            version="1.0.0",
            file_size=1000000,
            user=self.user,
            approved=True,
            file="path/to/file.zip",
            category=self.category,
        )

    def test_comment_saves_with_valid_data(self):
        comment = Comment(
            user=self.user,
            mod=self.mod,
            text="This is a comment",
        )
        comment.save()
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get(id=comment.id).text, "This is a comment")

    def test_comment_requires_user(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                mod=self.mod,
                text="This is a comment",
            )

    def test_comment_requires_mod(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                user=self.user,
                text="This is a comment",
            )

    def test_comment_requires_text(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                user=self.user,
                mod=self.mod,
            )

    def test_comment_text_length(self):
        valid_text = "a" * 1000
        invalid_text = "a" * 1001

        # Test with valid text length
        comment = Comment(
            user=self.user,
            mod=self.mod,
            text=valid_text,
        )
        comment.save()
        self.assertEqual(comment.text, valid_text)

        # Test with invalid text length
        with self.assertRaises(ValidationError):
            comment2 = Comment(
                user=self.user,
                mod=self.mod,
                text=invalid_text,
            )
            comment2.full_clean()  # This will trigger the validation
            comment2.save()

    def test_comment_creation_date(self):
        comment = Comment(
            user=self.user,
            mod=self.mod,
            text="This is a comment",
        )
        comment.save()
        self.assertIsNotNone(comment.comment_date)
