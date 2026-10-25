from datetime import timedelta

import pytest
from django.apps import apps
from django.db import models
from django.utils import timezone
from model_bakery import baker

from master.models import PlayerPosition
from match.models import Half, Match

pytestmark = pytest.mark.django_db


def test_held_manager_returns_past_alive_matches_only() -> None:
    now = timezone.now()
    past = baker.make(Match, held_datetime=now - timedelta(days=1))
    baker.make(Match, held_datetime=now + timedelta(days=1))
    deleted = baker.make(Match, held_datetime=now - timedelta(days=2))
    deleted.delete()
    assert list(Match.objects.held()) == [past]
    assert set(Match.all_objects.held()) == {past, deleted}


def test_has_been_held() -> None:
    now = timezone.now()
    past = baker.prepare(Match, held_datetime=now - timedelta(minutes=1))
    future = baker.prepare(Match, held_datetime=now + timedelta(minutes=1))
    assert past.has_been_held()
    assert not future.has_been_held()


def test_half_ordering_by_number() -> None:
    match = baker.make(Match)
    for number in (2, 1, 3):
        baker.make(Half, match=match, number=number)
    assert list(Half.objects.values_list('number', flat=True)) == [1, 2, 3]


def test_player_position_ordering_by_number() -> None:
    for number in (15, 1, 9):
        baker.make(PlayerPosition, number=number)
    assert list(PlayerPosition.objects.values_list('number', flat=True)) == [
        1,
        9,
        15,
    ]


@pytest.mark.parametrize(
    'model',
    [
        model
        for label in ('master', 'member', 'match')
        for model in apps.get_app_config(label).get_models()
    ],
    ids=lambda model: model.__name__,
)
def test_every_model_has_str(model: type[models.Model]) -> None:
    assert model.__str__ is not models.Model.__str__
    assert str(baker.make(model))
