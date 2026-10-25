from typing import Any

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseQuerySet(models.QuerySet):
    """QuerySet whose ``delete()`` is a soft delete.

    ``delete()`` sets ``deleted_at`` on every row (bulk ``UPDATE``) and returns
    the number of updated rows. Use ``hard_delete()`` to remove rows.
    """

    def delete(self) -> int:  # type: ignore[override]
        return super().update(deleted_at=timezone.now())

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> BaseQuerySet:
        return self.filter(deleted_at=None)

    def dead(self) -> BaseQuerySet:
        return self.exclude(deleted_at=None)


class BaseManager(models.Manager):
    """Manager that hides soft-deleted rows unless ``alive_only=False``."""

    def __init__(self, *args: Any, alive_only: bool = True, **kwargs: Any) -> None:
        self.alive_only = alive_only
        super().__init__(*args, **kwargs)

    def get_queryset(self) -> BaseQuerySet:
        queryset: BaseQuerySet = BaseQuerySet(self.model, using=self._db)
        if self.alive_only:
            return queryset.filter(deleted_at=None)
        return queryset

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return self.get_queryset().hard_delete()


class BaseModel(models.Model):
    """Abstract base with timestamps and soft delete.

    ``instance.delete()`` is a soft delete (only sets ``deleted_at``, related
    rows are left untouched), consistent with ``QuerySet.delete()``.
    ``instance.hard_delete()`` removes the row (and cascades) for real.
    """

    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)
    deleted_at = models.DateTimeField(_('削除日時'), blank=True, null=True)

    objects = BaseManager()
    all_objects = BaseManager(alive_only=False)

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=['deleted_at', 'updated_at'])
        return 1, {self._meta.label: 1}

    def hard_delete(
        self, using: Any = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        return super().delete(using=using, keep_parents=keep_parents)
