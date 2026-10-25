from django.contrib import admin

from common.admin import BaseAdmin, BaseTabularInline

from .models import (
    Half,
    Match,
    MatchFoulEvent,
    MatchPatternedEvent,
    MatchScoringEvent,
    MatchSwitchEvent,
    PlayerOnMatch,
    StaffOnMatch,
    TeamOnMatch,
)


class StaffOnMatchInline(BaseTabularInline):
    model = StaffOnMatch
    fields = []


class PlayerOnMatchInline(BaseTabularInline):
    model = PlayerOnMatch
    extra = 23
    fields = []


class TeamOnMatchAdmin(BaseAdmin):
    fields = []
    inlines = [StaffOnMatchInline, PlayerOnMatchInline]
    list_display = ('match', 'name', 'team_group')


admin.site.register(TeamOnMatch, TeamOnMatchAdmin)


class TeamOnMatchInline(BaseTabularInline):
    model = TeamOnMatch
    extra = 2
    min_num = 2
    max_num = 2
    fields = []


class HalfInline(BaseTabularInline):
    model = Half
    extra = 2
    fields = []


class MatchAdmin(BaseAdmin):
    fields = []
    inlines = [HalfInline, TeamOnMatchInline]
    list_display = ('match_type', 'held_datetime', 'has_been_held')


admin.site.register(Match, MatchAdmin)


class MatchPatternedEventInline(BaseTabularInline):
    model = MatchPatternedEvent
    extra = 1
    fields = []


class MatchSwitchEventInline(BaseTabularInline):
    model = MatchSwitchEvent
    extra = 1
    fields = []


class MatchScoringEventInline(BaseTabularInline):
    model = MatchScoringEvent
    extra = 1
    fields = []


class MatchFoulEventInline(BaseTabularInline):
    model = MatchFoulEvent
    extra = 1
    fields = []


class HalfAdmin(BaseAdmin):
    fields = []
    list_display = ('match', 'number', 'duration')
    inlines = [
        MatchPatternedEventInline,
        MatchSwitchEventInline,
        MatchScoringEventInline,
        MatchFoulEventInline,
    ]


admin.site.register(Half, HalfAdmin)
