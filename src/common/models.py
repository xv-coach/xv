from django.db import models
from django.utils import timezone


class BaseQuerySet(models.query.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.exclude(deleted_at=None)


class BaseManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return BaseQuerySet(self.model).filter(deleted_at=None)
        return BaseQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class BaseModel(models.Model):
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    deleted_at = models.DateTimeField('削除日時', blank=True, null=True)

    objects = BaseManager()
    all_objects = BaseManager(alive_only=False)

    class Meta:
        abstract = True
