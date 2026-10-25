from collections.abc import Callable

import pytest
from django.db import IntegrityError, transaction
from model_bakery import baker

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
