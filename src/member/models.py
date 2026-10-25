from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from master.models import PlayerPosition, StaffPosition


class TeamGroup(BaseModel):
    """
    チームグループ
    """

    name = models.CharField(max_length=35, verbose_name=_('チームグループ名'))
    is_my_team = models.BooleanField(verbose_name=_('自チームグループか'))

    class Meta:
        verbose_name = _('チームグループ')
        verbose_name_plural = _('チームグループ')
        db_table = 'rugby_team_group'

    def __str__(self) -> str:
        return self.name


class Team(BaseModel):
    """
    チーム
    """

    name = models.CharField(max_length=35, verbose_name=_('チーム名'))
    team_group = models.ForeignKey(
        TeamGroup, on_delete=models.PROTECT, verbose_name=_('チームグループ')
    )

    class Meta:
        verbose_name = _('チーム')
        verbose_name_plural = _('チーム')
        db_table = 'rugby_team'

    def __str__(self) -> str:
        return self.name


class Member(BaseModel):
    """
    チーム人員
    """

    family_name = models.CharField(max_length=35, verbose_name=_('姓'))
    first_name = models.CharField(max_length=35, verbose_name=_('名'))
    birthday = models.DateField(blank=True, null=True, verbose_name=_('誕生日'))
    team_group = models.ForeignKey(
        TeamGroup,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('所属チームグループ'),
    )
    staff_position = models.ManyToManyField(
        StaffPosition, blank=True, verbose_name=_('役職')
    )

    class Meta:
        verbose_name = _('チーム人員')
        verbose_name_plural = _('チーム人員')
        db_table = 'rugby_member'

    def __str__(self) -> str:
        return f'{self.family_name} {self.first_name}'


class PlayerProfile(BaseModel):
    """
    選手プロフィール
    """

    member = models.OneToOneField(
        Member, on_delete=models.CASCADE, verbose_name=_('人員')
    )
    height = models.DecimalField(verbose_name=_('身長'), max_digits=4, decimal_places=1)
    weight = models.DecimalField(verbose_name=_('体重'), max_digits=4, decimal_places=1)
    player_position = models.ManyToManyField(
        PlayerPosition, verbose_name=_('ポジション')
    )

    class Meta:
        verbose_name = _('選手プロフィール')
        verbose_name_plural = _('選手プロフィール')
        db_table = 'rugby_player_profile'

    def __str__(self) -> str:
        return str(self.member)
