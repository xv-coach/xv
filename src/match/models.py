from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import BaseManager, BaseModel
from master.models import (
    FieldStaff,
    FoulMethod,
    MatchSwitchEventType,
    MatchType,
    PatternType,
    ScoringMethod,
)
from member.models import Member, TeamGroup

# Unique constraints apply to live rows only, so a soft-deleted combination
# can be registered again (PostgreSQL partial unique indexes).
ALIVE = Q(deleted_at__isnull=True)

SAME_MATCH_ERROR = _('ハーフと同じ試合のものを選択してください。')


class HeldManager(BaseManager):
    def held(self, **kwargs: Any) -> models.QuerySet:
        """Matches whose ``held_datetime`` is now or in the past."""
        return self.filter(held_datetime__lte=timezone.now(), **kwargs)


class Match(BaseModel):
    """
    試合
    """

    held_datetime = models.DateTimeField(verbose_name=_('開催日時'))
    match_type = models.ForeignKey(
        MatchType, on_delete=models.PROTECT, verbose_name=_('試合種別')
    )
    referee = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('レフリー'),
        related_name='match_referee',
    )
    assistant_referee = models.ManyToManyField(
        Member,
        blank=True,
        verbose_name=_('アシスタントレフリー'),
        related_name='match_assistant_referee',
    )
    touch_judge = models.ManyToManyField(
        Member,
        blank=True,
        verbose_name=_('タッチジャッジ'),
        related_name='match_touch_judge',
    )

    objects: ClassVar[HeldManager] = HeldManager()
    all_objects: ClassVar[HeldManager] = HeldManager(alive_only=False)

    class Meta:
        verbose_name = _('試合')
        verbose_name_plural = _('試合')
        db_table = 'rugby_match'

    def __str__(self) -> str:
        return f'{self.held_datetime} {self.match_type}'

    def has_been_held(self) -> bool:
        return self.held_datetime < timezone.now()


class TeamOnMatch(BaseModel):
    """
    試合参加チーム
    """

    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name=_('試合'))
    name = models.CharField(max_length=35, verbose_name=_('チーム名'))
    team_group = models.ForeignKey(
        TeamGroup,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('チームグループ'),
    )
    display_first = models.BooleanField(null=False, verbose_name=_('優先表示'))

    class Meta:
        verbose_name = _('試合参加チーム')
        verbose_name_plural = _('試合参加チーム')
        db_table = 'rugby_team_on_match'
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'display_first'],
                condition=ALIVE,
                name='uniq_team_on_match_match_display_first',
            ),
        ]

    def __str__(self) -> str:
        return self.name


class StaffOnMatch(BaseModel):
    """
    試合参加スタッフ
    """

    team = models.ForeignKey(
        TeamOnMatch, on_delete=models.CASCADE, verbose_name=_('所属チーム')
    )
    field_staff = models.ForeignKey(
        FieldStaff, on_delete=models.PROTECT, verbose_name=_('フィールドスタッフ職')
    )
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, verbose_name=_('メンバー')
    )

    class Meta:
        verbose_name = _('試合参加スタッフ')
        verbose_name_plural = _('試合参加スタッフ')
        db_table = 'rugby_staff_on_match'
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'member'],
                condition=ALIVE,
                name='uniq_staff_on_match_team_member',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.team} {self.field_staff} {self.member}'


class PlayerOnMatch(BaseModel):
    """
    試合登録プレイヤー
    """

    team = models.ForeignKey(
        TeamOnMatch, on_delete=models.CASCADE, verbose_name=_('所属チーム')
    )
    position_number = models.PositiveIntegerField(verbose_name=_('背番号'))
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, verbose_name=_('メンバー')
    )

    class Meta:
        verbose_name = _('試合登録プレイヤー')
        verbose_name_plural = _('試合登録プレイヤー')
        db_table = 'rugby_player_on_match'
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'position_number'],
                condition=ALIVE,
                name='uniq_player_on_match_team_position_number',
            ),
            models.UniqueConstraint(
                fields=['team', 'member'],
                condition=ALIVE,
                name='uniq_player_on_match_team_member',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.team} #{self.position_number} {self.member}'


class Half(BaseModel):
    """
    ハーフ
    """

    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name=_('試合'))
    duration = models.DurationField(verbose_name=_('時間'))
    number = models.IntegerField(verbose_name=_('序数'))

    class Meta:
        verbose_name = _('ハーフ')
        verbose_name_plural = _('ハーフ')
        db_table = 'rugby_half'
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'number'],
                condition=ALIVE,
                name='uniq_half_match_number',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.match} 第{self.number}ハーフ'


class MatchEvent(BaseModel):
    """
    試合イベント
    """

    half = models.ForeignKey(Half, on_delete=models.PROTECT, verbose_name=_('ハーフ'))
    duration = models.DurationField(verbose_name=_('経過時間'))

    class Meta:
        verbose_name = _('試合イベント')
        verbose_name_plural = _('試合イベント')
        abstract = True

    def __str__(self) -> str:
        return f'{self.half} {self.duration}'

    def _match_id(self) -> int | None:
        """``match_id`` of this event's half, or None if no half is set yet."""
        if self.half_id is None:
            return None
        return self.half.match_id

    def _validate_players_in_match(
        self, errors: dict[str, Any], *field_names: str
    ) -> None:
        """Every given ``PlayerOnMatch`` field must belong to the half's match."""
        match_id = self._match_id()
        if match_id is None:
            return
        for name in field_names:
            player: PlayerOnMatch | None = getattr(self, name)
            if player is not None and player.team.match_id != match_id:
                errors[name] = SAME_MATCH_ERROR

    def _validate_events_in_match(
        self, errors: dict[str, Any], *field_names: str
    ) -> None:
        """Every given related event field must belong to the half's match."""
        match_id = self._match_id()
        if match_id is None:
            return
        for name in field_names:
            event: MatchEvent | None = getattr(self, name)
            if event is not None and event.half.match_id != match_id:
                errors[name] = SAME_MATCH_ERROR


class MatchPatternedEvent(MatchEvent):
    """
    通常試合イベント
    """

    event_type = models.ForeignKey(
        PatternType, on_delete=models.PROTECT, verbose_name=_('試合イベント種別')
    )

    class Meta:
        verbose_name = _('通常試合イベント')
        verbose_name_plural = _('通常試合イベント')
        db_table = 'rugby_match_patterned_event'

    def __str__(self) -> str:
        return f'{super().__str__()} {self.event_type}'


class MatchSwitchEvent(MatchEvent):
    """
    試合中交替/入替イベント
    """

    event_type = models.ForeignKey(
        MatchSwitchEventType,
        on_delete=models.PROTECT,
        verbose_name=_('試合中交替/入替イベント種別'),
    )
    out_member = models.ForeignKey(
        PlayerOnMatch,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('退場メンバー'),
        related_name='match_out',
    )
    in_member = models.ForeignKey(
        PlayerOnMatch,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('出場メンバー'),
        related_name='match_in',
    )

    class Meta:
        verbose_name = _('試合中交替/入替イベント')
        verbose_name_plural = _('試合中交替/入替イベント')
        db_table = 'rugby_match_switch_event'

    def __str__(self) -> str:
        return f'{super().__str__()} {self.event_type}'

    def clean(self) -> None:
        super().clean()
        errors: dict[str, Any] = {}
        self._validate_players_in_match(errors, 'out_member', 'in_member')
        if not errors and self.out_member is not None and self.in_member is not None:
            if self.out_member.pk == self.in_member.pk:
                errors['in_member'] = _(
                    '退場メンバーと出場メンバーには別の選手を選択してください。'
                )
            elif self.out_member.team_id != self.in_member.team_id:
                errors['in_member'] = _(
                    '退場メンバーと同じチームの選手を選択してください。'
                )
        if errors:
            raise ValidationError(errors)


class MatchScoringEvent(MatchEvent):
    """
    試合中得点イベント
    """

    method = models.ForeignKey(
        ScoringMethod, on_delete=models.PROTECT, verbose_name=_('得点手法')
    )
    player = models.ForeignKey(
        PlayerOnMatch, on_delete=models.PROTECT, verbose_name=_('得点メンバー')
    )
    is_no_kick = models.BooleanField(verbose_name=_('キック蹴らず'))

    class Meta:
        verbose_name = _('試合中得点イベント')
        verbose_name_plural = _('試合中得点イベント')
        db_table = 'rugby_match_scoring_event'

    def __str__(self) -> str:
        return f'{super().__str__()} {self.method} {self.player}'

    def clean(self) -> None:
        super().clean()
        errors: dict[str, Any] = {}
        if self.player_id is not None:
            self._validate_players_in_match(errors, 'player')
        if errors:
            raise ValidationError(errors)


class MatchFoulEvent(MatchEvent):
    """
    試合中反則イベント
    """

    class Card(models.TextChoices):
        SAFE = 'safe', _('No Card')
        YELLOW = 'yellow', _('Yellow Card')
        RED = 'red', _('Red Card')

    method = models.ForeignKey(
        FoulMethod, on_delete=models.PROTECT, verbose_name=_('反則手法')
    )
    player = models.ForeignKey(
        PlayerOnMatch, on_delete=models.PROTECT, verbose_name=_('反則メンバー')
    )
    card_choice = models.CharField(
        max_length=6, choices=Card.choices, verbose_name=_('カード')
    )
    out_event = models.ForeignKey(
        MatchSwitchEvent,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('退場イベント'),
    )
    penalty_try = models.ForeignKey(
        MatchScoringEvent,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_('ペナルティトライイベント'),
    )

    class Meta:
        verbose_name = _('試合中反則イベント')
        verbose_name_plural = _('試合中反則イベント')
        db_table = 'rugby_match_foul_event'

    def __str__(self) -> str:
        return (
            f'{super().__str__()} {self.method} {self.player} '
            f'{self.get_card_choice_display()}'
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, Any] = {}
        if self.player_id is not None:
            self._validate_players_in_match(errors, 'player')
        self._validate_events_in_match(errors, 'out_event', 'penalty_try')
        if errors:
            raise ValidationError(errors)
