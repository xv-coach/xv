from dataclasses import dataclass

import pytest
from model_bakery import baker

from match.models import Half, Match, PlayerOnMatch, TeamOnMatch


@dataclass
class MatchSetup:
    match: Match
    half: Half
    home: TeamOnMatch
    away: TeamOnMatch
    home_player: PlayerOnMatch
    home_sub: PlayerOnMatch
    away_player: PlayerOnMatch


def make_match_setup() -> MatchSetup:
    match = baker.make(Match)
    home = baker.make(TeamOnMatch, match=match, display_first=True)
    away = baker.make(TeamOnMatch, match=match, display_first=False)
    return MatchSetup(
        match=match,
        half=baker.make(Half, match=match, number=1),
        home=home,
        away=away,
        home_player=baker.make(PlayerOnMatch, team=home, position_number=1),
        home_sub=baker.make(PlayerOnMatch, team=home, position_number=16),
        away_player=baker.make(PlayerOnMatch, team=away, position_number=1),
    )


@pytest.fixture
def match_setup(db: None) -> MatchSetup:
    return make_match_setup()


@pytest.fixture
def other_match_setup(db: None) -> MatchSetup:
    return make_match_setup()
