from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MatchConfig(AppConfig):
    name = 'match'
    verbose_name = _('試合')
