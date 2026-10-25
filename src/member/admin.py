from django.contrib import admin

from common.admin import BaseAdmin, BaseTabularInline

from .models import Member, PlayerProfile, Team, TeamGroup


class TeamInline(BaseTabularInline):
    model = Team
    fields = []


class TeamGroupAdmin(BaseAdmin):
    list_display = ('name',)
    fields = []
    inlines = [TeamInline]


admin.site.register(TeamGroup, TeamGroupAdmin)


class PlayerProfileInline(BaseTabularInline):
    model = PlayerProfile
    fields = []


class MemberAdmin(BaseAdmin):
    list_display = ('family_name', 'first_name', 'team_group')
    fields = []
    inlines = [PlayerProfileInline]


admin.site.register(Member, MemberAdmin)
