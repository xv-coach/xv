from django.test import TestCase
from django.urls import reverse

from master.models import StaffPosition


class SoftDeleteSmokeTest(TestCase):
    def test_queryset_delete_is_soft(self):
        StaffPosition.objects.create(name='監督')
        StaffPosition.objects.all().delete()
        self.assertEqual(StaffPosition.objects.count(), 0)
        self.assertEqual(StaffPosition.all_objects.count(), 1)


class AdminSmokeTest(TestCase):
    def test_admin_login_page(self):
        response = self.client.get(reverse('admin:login'))
        self.assertEqual(response.status_code, 200)
