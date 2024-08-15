import uuid
from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Mod, ModImage, Category

User = get_user_model()


class ModModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', email=f'{uuid.uuid4()}@example.com')
        self.category = Category.objects.create(name='Test Category')
        self.mod = Mod.objects.create(
            id=1,
            title='Test Mod',
            short_desc='Short description',
            description='Long description',
            version='1.0.0',
            file_size=1000000,
            user=self.user,
            approved=True
        )
        self.mod.categories.add(self.category)

    def test_unique_email_constraint(self):
        user1 = User.objects.create(username='user1', email=f'{uuid.uuid4()}@example.com')
        with self.assertRaises(IntegrityError):
            User.objects.create(username='user2', email=user1.email)

    def test_mod_saves_with_thumbnail(self):
        image = ModImage.objects.create(mod=self.mod, image='path/to/image.jpg', is_thumbnail=True)
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.thumbnail, image.image.url)

    def test_only_one_thumbnail_per_mod(self):
        image1 = ModImage.objects.create(mod=self.mod, image='path/to/image1.jpg', is_thumbnail=True)
        image2 = ModImage.objects.create(mod=self.mod, image='path/to/image2.jpg', is_thumbnail=True)
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.thumbnail, image2.image.url)
        self.assertFalse(ModImage.objects.get(id=image1.id).is_thumbnail)

    def test_mod_without_thumbnail(self):
        image = ModImage.objects.create(mod=self.mod, image='path/to/image.jpg', is_thumbnail=False)
        self.mod.refresh_from_db()
        self.assertIsNone(self.mod.thumbnail)

    def test_mod_saves_with_multiple_categories(self):
        category2 = Category.objects.create(name='Another Category')
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
                title='Invalid Mod',
                short_desc='Short description',
                description='Long description',
                version='1.0.0',
                file_size='invalid_size',
                user=User.objects.create(username='anotheruser', email=f'{uuid.uuid4()}@example.com'),
                approved=True
            )

    def test_mod_with_negative_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=2,
                title='Invalid Mod',
                short_desc='Short description',
                description='Long description',
                version='1.0.0',
                file_size=-1,
                user=self.user,
                approved=True
            )

    def test_mod_with_too_large_file_size(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=2,
                title='Invalid Mod',
                short_desc='Short description',
                description='Long description',
                version='1.0.0',
                file_size=1000000000000,
                user=self.user,
                approved=True
            )

    def test_mod_with_512mb_file_size(self):
        mod = Mod.objects.create(
            id=2,
            title='Valid Mod',
            short_desc='Short description',
            description='Long description',
            version='1.0.0',
            file_size=536870912,
            user=self.user,
            approved=True
        )
        self.assertEqual(mod.file_size, 536870912)

    def test_mod_with_duplicate_title(self):
        Mod.objects.create(
            id=3,
            title='Test Mod',
            short_desc='Short description',
            description='Long description',
            version='1.0.0',
            file_size=1000000,
            user=User.objects.create(username='anotheruser', email=f'{uuid.uuid4()}@example.com'),
            approved=True
        )
        self.assertEqual(Mod.objects.filter(title='Test Mod').count(), 2)


    def test_mod_with_duplicate_user(self):
        Mod.objects.create(
            id=3,
            title='Another Mod',
            short_desc='Short description',
            description='Long description',
            version='1.0.0',
            file_size=1000000,
            user=self.user,
            approved=True
        )
        self.assertEqual(Mod.objects.filter(user=self.user).count(), 2)


    def test_mod_with_invalid_version(self):
        with self.assertRaises(ValueError):
            Mod.objects.create(
                id=3,
                title='Invalid Mod',
                short_desc='Short description',
                description='Long description',
                version=1,
                file_size=1000000,
                user=self.user,
                approved=True
            )