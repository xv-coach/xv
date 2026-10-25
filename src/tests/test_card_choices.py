import pytest
from model_bakery import baker

from match.models import MatchFoulEvent
from tests.conftest import MatchSetup

Card = MatchFoulEvent.Card


def test_card_stored_values_are_unchanged() -> None:
    assert Card.values == ['safe', 'yellow', 'red']
    assert [str(label) for label in Card.labels] == [
        'No Card',
        'Yellow Card',
        'Red Card',
    ]


def test_card_field_uses_text_choices() -> None:
    field = MatchFoulEvent._meta.get_field('card_choice')
    assert field.choices is not None
    assert [value for value, _ in field.choices] == Card.values


@pytest.mark.django_db
def test_card_is_stored_as_plain_string(match_setup: MatchSetup) -> None:
    event = baker.make(
        MatchFoulEvent,
        half=match_setup.half,
        player=match_setup.home_player,
        card_choice=Card.YELLOW,
    )
    assert (
        MatchFoulEvent.objects.values_list('card_choice', flat=True).get(pk=event.pk)
        == 'yellow'
    )
    event.refresh_from_db()
    assert event.card_choice == Card.YELLOW
    assert event.get_card_choice_display() == 'Yellow Card'
