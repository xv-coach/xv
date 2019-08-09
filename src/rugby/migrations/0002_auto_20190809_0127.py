# Generated by Django 2.2 on 2019-08-08 16:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rugby', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='fieldstaff',
            table='rugby_field_staff',
        ),
        migrations.AlterModelTable(
            name='foulmethod',
            table='rugby_foul_method',
        ),
        migrations.AlterModelTable(
            name='half',
            table='rugby_half',
        ),
        migrations.AlterModelTable(
            name='match',
            table='rugby_match',
        ),
        migrations.AlterModelTable(
            name='matchfoulevent',
            table='rugby_match_foul_event',
        ),
        migrations.AlterModelTable(
            name='matchpatternedevent',
            table='rugby_match_patterned_event',
        ),
        migrations.AlterModelTable(
            name='matchscoringevent',
            table='rugby_match_scoring_event',
        ),
        migrations.AlterModelTable(
            name='matchswitchevent',
            table='rugby_match_switch_event',
        ),
        migrations.AlterModelTable(
            name='matchswitcheventtype',
            table='rugby_match_switch_event_type',
        ),
        migrations.AlterModelTable(
            name='matchtype',
            table='rugby_match_type',
        ),
        migrations.AlterModelTable(
            name='member',
            table='rugby_member',
        ),
        migrations.AlterModelTable(
            name='patterntype',
            table='rugby_pattern_type',
        ),
        migrations.AlterModelTable(
            name='playeronmatch',
            table='rugby_player_on_match',
        ),
        migrations.AlterModelTable(
            name='playerposition',
            table='rugby_player_position',
        ),
        migrations.AlterModelTable(
            name='playerprofile',
            table='rugby_player_profile',
        ),
        migrations.AlterModelTable(
            name='scoringmethod',
            table='rugby_scoring_method',
        ),
        migrations.AlterModelTable(
            name='staffonmatch',
            table='rugby_staff_on_match',
        ),
        migrations.AlterModelTable(
            name='staffposition',
            table='rugby_staff_position',
        ),
        migrations.AlterModelTable(
            name='team',
            table='rugby_team',
        ),
        migrations.AlterModelTable(
            name='teamgroup',
            table='rugby_team_group',
        ),
        migrations.AlterModelTable(
            name='teamonmatch',
            table='rugby_team_on_match',
        ),
    ]