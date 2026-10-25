import pytest

from master.models import StaffPosition

pytestmark = pytest.mark.django_db


def test_queryset_delete_is_soft() -> None:
    StaffPosition.objects.create(name='監督')
    StaffPosition.objects.all().delete()
    assert StaffPosition.objects.count() == 0
    assert StaffPosition.all_objects.count() == 1


def test_queryset_delete_returns_updated_row_count() -> None:
    StaffPosition.objects.create(name='監督')
    StaffPosition.objects.create(name='コーチ')
    assert StaffPosition.objects.all().delete() == 2


def test_instance_delete_is_soft() -> None:
    position = StaffPosition.objects.create(name='監督')
    assert position.delete() == (1, {'master.StaffPosition': 1})
    position.refresh_from_db()
    assert position.is_deleted
    assert position.deleted_at is not None
    assert not StaffPosition.objects.filter(pk=position.pk).exists()
    assert StaffPosition.all_objects.filter(pk=position.pk).exists()


def test_instance_hard_delete_removes_row() -> None:
    position = StaffPosition.objects.create(name='監督')
    count, _ = position.hard_delete()
    assert count == 1
    assert not StaffPosition.all_objects.filter(name='監督').exists()


def test_manager_hard_delete_removes_alive_rows_only() -> None:
    StaffPosition.objects.create(name='監督')
    StaffPosition.objects.create(name='コーチ').delete()
    StaffPosition.objects.hard_delete()
    assert list(StaffPosition.all_objects.values_list('name', flat=True)) == ['コーチ']


def test_alive_and_dead() -> None:
    StaffPosition.objects.create(name='監督')
    StaffPosition.objects.create(name='コーチ').delete()
    everything = StaffPosition.all_objects.get_queryset()
    assert [p.name for p in everything.alive()] == ['監督']
    assert [p.name for p in everything.dead()] == ['コーチ']
