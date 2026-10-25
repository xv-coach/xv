from django.db import models

from common.models import BaseModel


class PlayerPosition(BaseModel):
    """
    ポジション
    """

    number = models.IntegerField(verbose_name='背番号')
    name = models.CharField(max_length=35, verbose_name='ポジション名')
    is_front_row = models.BooleanField(verbose_name='フロントロー')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'ポジション'
        db_table = 'rugby_player_position'


class StaffPosition(BaseModel):
    """
    役職
    """

    name = models.CharField(max_length=35, verbose_name='役職名')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '役職'
        db_table = 'rugby_staff_position'


class FieldStaff(BaseModel):
    """
    フィールドスタッフ職
    """

    name = models.CharField(max_length=35, verbose_name='フィールドスタッフ職')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'フィールドスタッフ'
        db_table = 'rugby_field_staff'


class MatchType(BaseModel):
    """
    試合形式
    """

    name = models.CharField(max_length=35, verbose_name='試合形式名称')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '試合形式'
        db_table = 'rugby_match_type'


class PatternType(BaseModel):
    """
    試合イベントパターン
    """

    name = models.CharField(max_length=35, verbose_name='イベント名')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '試合イベントパターン'
        db_table = 'rugby_pattern_type'


class MatchSwitchEventType(BaseModel):
    """
    試合中交替/入替イベント種別
    """

    name = models.CharField(max_length=35, verbose_name='試合中交替/入替イベント名称')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '試合中交替/入替イベント種別'
        db_table = 'rugby_match_switch_event_type'


class ScoringMethod(BaseModel):
    """
    得点手法
    """

    name = models.CharField(max_length=35, verbose_name='得点手法名')
    short_letter = models.CharField(max_length=2, verbose_name='得点コード')
    point = models.IntegerField(verbose_name='得点')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '得点手法'
        db_table = 'rugby_scoring_method'


class FoulMethod(BaseModel):
    """
    反則
    """

    name = models.CharField(max_length=35, verbose_name='反則名')
    is_penalty = models.BooleanField(verbose_name='重度な反則か')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '反則'
        db_table = 'rugby_foul_method'
