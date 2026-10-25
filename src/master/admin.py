from django.contrib import admin

from common.admin import BaseAdmin

from .models import (
    FieldStaff,
    FoulMethod,
    MatchSwitchEventType,
    MatchType,
    PatternType,
    PlayerPosition,
    ScoringMethod,
    StaffPosition,
)


class PlayerPositionAdmin(BaseAdmin):
    list_display = ('number', 'name', 'is_front_row')
    ordering = ['number']


admin.site.register(PlayerPosition, PlayerPositionAdmin)


class StaffPositionAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []


admin.site.register(StaffPosition, StaffPositionAdmin)


class FieldStaffAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []


admin.site.register(FieldStaff, FieldStaffAdmin)


class MatchTypeAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []


admin.site.register(MatchType, MatchTypeAdmin)


class PatternTypeAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []


admin.site.register(PatternType, PatternTypeAdmin)


class MatchSwitchEventTypeAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []


admin.site.register(MatchSwitchEventType, MatchSwitchEventTypeAdmin)


class ScoringMethodAdmin(BaseAdmin):
    list_display = ('short_letter', 'name', 'point')
    fields = []


admin.site.register(ScoringMethod, ScoringMethodAdmin)


class FoulMethodAdmin(BaseAdmin):
    list_display = ('name', 'is_penalty')
    fields = []


admin.site.register(FoulMethod, FoulMethodAdmin)
