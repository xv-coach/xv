import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from match.models import MatchFoulEvent, MatchScoringEvent, MatchSwitchEvent
from tests.conftest import MatchSetup

pytestmark = pytest.mark.django_db


def error_fields(exc: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    return set(exc.value.message_dict)


def test_scoring_event_player_in_same_match_is_valid(match_setup: MatchSetup) -> None:
    event = baker.prepare(
        MatchScoringEvent,
        half=match_setup.half,
        player=match_setup.away_player,
        _save_related=True,
    )
    event.full_clean()


def test_scoring_event_player_from_other_match_is_invalid(
    match_setup: MatchSetup, other_match_setup: MatchSetup
) -> None:
    event = baker.prepare(
        MatchScoringEvent,
        half=match_setup.half,
        player=other_match_setup.home_player,
        _save_related=True,
    )
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert error_fields(exc) == {'player'}


def test_switch_event_valid(match_setup: MatchSetup) -> None:
    event = baker.prepare(
        MatchSwitchEvent,
        half=match_setup.half,
        out_member=match_setup.home_player,
        in_member=match_setup.home_sub,
        _save_related=True,
    )
    event.full_clean()


def test_switch_event_members_from_other_match_are_invalid(
    match_setup: MatchSetup, other_match_setup: MatchSetup
) -> None:
    event = baker.prepare(
        MatchSwitchEvent,
        half=match_setup.half,
        out_member=other_match_setup.home_player,
        in_member=other_match_setup.home_sub,
        _save_related=True,
    )
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert error_fields(exc) == {'out_member', 'in_member'}


def test_switch_event_members_must_be_same_team(match_setup: MatchSetup) -> None:
    event = baker.prepare(
        MatchSwitchEvent,
        half=match_setup.half,
        out_member=match_setup.home_player,
        in_member=match_setup.away_player,
        _save_related=True,
    )
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert error_fields(exc) == {'in_member'}


def test_switch_event_members_must_differ(match_setup: MatchSetup) -> None:
    event = baker.prepare(
        MatchSwitchEvent,
        half=match_setup.half,
        out_member=match_setup.home_player,
        in_member=match_setup.home_player,
        _save_related=True,
    )
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert error_fields(exc) == {'in_member'}


def test_foul_event_valid_with_related_events(match_setup: MatchSetup) -> None:
    out_event = baker.make(
        MatchSwitchEvent,
        half=match_setup.half,
        out_member=match_setup.away_player,
        in_member=None,
    )
    penalty_try = baker.make(
        MatchScoringEvent, half=match_setup.half, player=match_setup.home_player
    )
    event = baker.prepare(
        MatchFoulEvent,
        half=match_setup.half,
        player=match_setup.away_player,
        out_event=out_event,
        penalty_try=penalty_try,
        card_choice=MatchFoulEvent.Card.RED,
        _save_related=True,
    )
    event.full_clean()


def test_foul_event_cross_match_references_are_invalid(
    match_setup: MatchSetup, other_match_setup: MatchSetup
) -> None:
    other = other_match_setup
    out_event = baker.make(MatchSwitchEvent, half=other.half, out_member=None)
    penalty_try = baker.make(
        MatchScoringEvent, half=other.half, player=other.home_player
    )
    event = baker.prepare(
        MatchFoulEvent,
        half=match_setup.half,
        player=other.away_player,
        out_event=out_event,
        penalty_try=penalty_try,
        card_choice=MatchFoulEvent.Card.YELLOW,
        _save_related=True,
    )
    with pytest.raises(ValidationError) as exc:
        event.full_clean()
    assert error_fields(exc) == {'player', 'out_event', 'penalty_try'}
