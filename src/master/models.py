from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class PlayerPosition(BaseModel):
    """
    ポジション
    """

    number = models.IntegerField(verbose_name=_('背番号'))
    name = models.CharField(max_length=35, verbose_name=_('ポジション名'))
    is_front_row = models.BooleanField(verbose_name=_('フロントロー'))

    class Meta:
        verbose_name = _('ポジション')
        verbose_name_plural = _('ポジション')
        db_table = 'rugby_player_position'
        ordering = ['number']

    def __str__(self) -> str:
        return self.name


class StaffPosition(BaseModel):
    """
    役職
    """

    name = models.CharField(max_length=35, verbose_name=_('役職名'))

    class Meta:
        verbose_name = _('役職')
        verbose_name_plural = _('役職')
        db_table = 'rugby_staff_position'

    def __str__(self) -> str:
        return self.name


class FieldStaff(BaseModel):
    """
    フィールドスタッフ職
    """

    name = models.CharField(max_length=35, verbose_name=_('フィールドスタッフ職'))

    class Meta:
        verbose_name = _('フィールドスタッフ')
        verbose_name_plural = _('フィールドスタッフ')
        db_table = 'rugby_field_staff'

    def __str__(self) -> str:
        return self.name


class MatchType(BaseModel):
    """
    試合形式
    """

    name = models.CharField(max_length=35, verbose_name=_('試合形式名称'))

    class Meta:
        verbose_name = _('試合形式')
        verbose_name_plural = _('試合形式')
        db_table = 'rugby_match_type'

    def __str__(self) -> str:
        return self.name


class PatternType(BaseModel):
    """
    試合イベントパターン
    """

    name = models.CharField(max_length=35, verbose_name=_('イベント名'))

    class Meta:
        verbose_name = _('試合イベントパターン')
        verbose_name_plural = _('試合イベントパターン')
        db_table = 'rugby_pattern_type'

    def __str__(self) -> str:
        return self.name


class MatchSwitchEventType(BaseModel):
    """
    試合中交替/入替イベント種別
    """

    name = models.CharField(
        max_length=35, verbose_name=_('試合中交替/入替イベント名称')
    )

    class Meta:
        verbose_name = _('試合中交替/入替イベント種別')
        verbose_name_plural = _('試合中交替/入替イベント種別')
        db_table = 'rugby_match_switch_event_type'

    def __str__(self) -> str:
        return self.name


class ScoringMethod(BaseModel):
    """
    得点手法
    """

    name = models.CharField(max_length=35, verbose_name=_('得点手法名'))
    short_letter = models.CharField(max_length=2, verbose_name=_('得点コード'))
    point = models.IntegerField(verbose_name=_('得点'))

    class Meta:
        verbose_name = _('得点手法')
        verbose_name_plural = _('得点手法')
        db_table = 'rugby_scoring_method'

    def __str__(self) -> str:
        return self.name


class FoulMethod(BaseModel):
    """
    反則
    """

    name = models.CharField(max_length=35, verbose_name=_('反則名'))
    is_penalty = models.BooleanField(verbose_name=_('重度な反則か'))

    class Meta:
        verbose_name = _('反則')
        verbose_name_plural = _('反則')
        db_table = 'rugby_foul_method'

    def __str__(self) -> str:
        return self.name
