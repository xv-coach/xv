from collections.abc import Callable
from datetime import timedelta
from typing import Any

import pytest
from django.contrib import admin
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from model_bakery import baker

from common.models import BaseModel
from match.models import Half, PlayerOnMatch, StaffOnMatch, TeamOnMatch
from tests.conftest import MatchSetup


def assert_integrity_error(create: Callable[[], object]) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        create()


def test_team_on_match_display_first_is_unique_per_match(
    match_setup: MatchSetup,
) -> None:
    assert_integrity_error(
        lambda: baker.make(TeamOnMatch, match=match_setup.match, display_first=True)
    )


def test_staff_on_match_member_is_unique_per_team(match_setup: MatchSetup) -> None:
    staff = baker.make(StaffOnMatch, team=match_setup.home)
    assert_integrity_error(
        lambda: baker.make(StaffOnMatch, team=match_setup.home, member=staff.member)
    )


def test_player_on_match_position_number_is_unique_per_team(
    match_setup: MatchSetup,
) -> None:
    assert_integrity_error(
        lambda: baker.make(PlayerOnMatch, team=match_setup.home, position_number=1)
    )


def test_player_on_match_member_is_unique_per_team(match_setup: MatchSetup) -> None:
    assert_integrity_error(
        lambda: baker.make(
            PlayerOnMatch,
            team=match_setup.home,
            position_number=2,
            member=match_setup.home_player.member,
        )
    )


def test_same_member_and_number_allowed_on_other_team(
    match_setup: MatchSetup,
) -> None:
    baker.make(
        PlayerOnMatch,
        team=match_setup.away,
        position_number=16,
        member=match_setup.home_sub.member,
    )


def test_half_number_is_unique_per_match(match_setup: MatchSetup) -> None:
    assert_integrity_error(lambda: baker.make(Half, match=match_setup.match, number=1))


def test_constraint_names() -> None:
    names = {
        constraint.name
        for model in (TeamOnMatch, StaffOnMatch, PlayerOnMatch, Half)
        for constraint in model._meta.constraints
    }
    assert names == {
        'uniq_team_on_match_match_display_first',
        'uniq_staff_on_match_team_member',
        'uniq_player_on_match_team_position_number',
        'uniq_player_on_match_team_member',
        'uniq_half_match_number',
    }


# --- Soft-deleted rows are excluded (condition=Q(deleted_at__isnull=True)) ---

DuplicateFactory = Callable[[MatchSetup], tuple[BaseModel, Callable[[], Any]]]


def _team_on_match(s: MatchSetup) -> tuple[BaseModel, Callable[[], Any]]:
    return s.home, lambda: baker.prepare(
        TeamOnMatch,
        match=s.match,
        display_first=True,
        team_group=s.home.team_group or baker.make('member.TeamGroup'),
    )


def _staff_on_match(s: MatchSetup) -> tuple[BaseModel, Callable[[], Any]]:
    staff = baker.make(StaffOnMatch, team=s.home)
    return staff, lambda: baker.prepare(
        StaffOnMatch,
        team=s.home,
        member=staff.member,
        field_staff=staff.field_staff,
    )


def _player_position_number(
    s: MatchSetup,
) -> tuple[BaseModel, Callable[[], Any]]:
    return s.home_player, lambda: baker.prepare(
        PlayerOnMatch, team=s.home, position_number=1, _save_related=True
    )


def _player_member(s: MatchSetup) -> tuple[BaseModel, Callable[[], Any]]:
    return s.home_player, lambda: baker.prepare(
        PlayerOnMatch, team=s.home, position_number=2, member=s.home_player.member
    )


def _half(s: MatchSetup) -> tuple[BaseModel, Callable[[], Any]]:
    return s.half, lambda: baker.prepare(
        Half, match=s.match, number=1, duration=timedelta(minutes=40)
    )


DUPLICATES: dict[str, DuplicateFactory] = {
    'uniq_team_on_match_match_display_first': _team_on_match,
    'uniq_staff_on_match_team_member': _staff_on_match,
    'uniq_player_on_match_team_position_number': _player_position_number,
    'uniq_player_on_match_team_member': _player_member,
    'uniq_half_match_number': _half,
}


@pytest.mark.parametrize('factory', DUPLICATES.values(), ids=DUPLICATES.keys())
def test_live_duplicate_fails_full_clean(
    match_setup: MatchSetup, factory: DuplicateFactory
) -> None:
    _, make_duplicate = factory(match_setup)
    with pytest.raises(ValidationError) as exc:
        make_duplicate().full_clean()
    assert exc.value.message_dict.get(NON_FIELD_ERRORS)


@pytest.mark.parametrize('factory', DUPLICATES.values(), ids=DUPLICATES.keys())
def test_live_duplicate_fails_in_db(
    match_setup: MatchSetup, factory: DuplicateFactory
) -> None:
    _, make_duplicate = factory(match_setup)
    duplicate = make_duplicate()
    assert_integrity_error(duplicate.save)


@pytest.mark.parametrize('factory', DUPLICATES.values(), ids=DUPLICATES.keys())
def test_can_reregister_after_soft_delete(
    match_setup: MatchSetup, factory: DuplicateFactory
) -> None:
    original, make_duplicate = factory(match_setup)
    original.delete()  # soft delete
    duplicate = make_duplicate()
    duplicate.full_clean()
    duplicate.save()
    model = type(original)
    assert model.all_objects.filter(pk=original.pk).exists()
    assert model.objects.filter(pk=duplicate.pk).exists()


def test_restoring_soft_deleted_row_conflicts_with_live_duplicate(
    match_setup: MatchSetup,
) -> None:
    original = match_setup.half
    original.delete()
    baker.make(Half, match=match_setup.match, number=1)
    original.deleted_at = None
    assert_integrity_error(original.save)


def _admin_half_form(rf: RequestFactory, admin_user: Any, number: int) -> Any:
    request = rf.get('/')
    request.user = admin_user
    form_class = admin.site._registry[Half].get_form(request)
    return form_class(data={'match': '', 'duration': '00:40:00', 'number': str(number)})


def test_admin_form_rejects_live_duplicate(
    match_setup: MatchSetup, rf: RequestFactory, admin_user: Any
) -> None:
    form = _admin_half_form(rf, admin_user, 1)
    form.data = {**form.data, 'match': str(match_setup.match.pk)}
    assert not form.is_valid()
    assert form.non_field_errors()


def test_admin_form_accepts_after_soft_delete(
    match_setup: MatchSetup, rf: RequestFactory, admin_user: Any
) -> None:
    match_setup.half.delete()
    form = _admin_half_form(rf, admin_user, 1)
    form.data = {**form.data, 'match': str(match_setup.match.pk)}
    assert form.is_valid(), form.errors
    form.save()
    assert Half.all_objects.filter(match=match_setup.match, number=1).count() == 2
