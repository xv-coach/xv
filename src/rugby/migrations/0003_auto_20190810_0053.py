# Generated by Django 2.2 on 2019-08-09 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rugby', '0002_auto_20190809_0127'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fieldstaff',
            options={'verbose_name_plural': 'フィールドスタッフ'},
        ),
        migrations.AlterModelOptions(
            name='foulmethod',
            options={'verbose_name_plural': '反則'},
        ),
        migrations.AlterModelOptions(
            name='half',
            options={'verbose_name_plural': 'ハーフ'},
        ),
        migrations.AlterModelOptions(
            name='match',
            options={'verbose_name_plural': '試合'},
        ),
        migrations.AlterModelOptions(
            name='matchfoulevent',
            options={'verbose_name_plural': '試合中反則イベント'},
        ),
        migrations.AlterModelOptions(
            name='matchpatternedevent',
            options={'verbose_name_plural': '通常試合イベント'},
        ),
        migrations.AlterModelOptions(
            name='matchscoringevent',
            options={'verbose_name_plural': '試合中得点イベント'},
        ),
        migrations.AlterModelOptions(
            name='matchswitchevent',
            options={'verbose_name_plural': '試合中交替/入替イベント'},
        ),
        migrations.AlterModelOptions(
            name='matchswitcheventtype',
            options={'verbose_name_plural': '試合中交替/入替イベント種別'},
        ),
        migrations.AlterModelOptions(
            name='matchtype',
            options={'verbose_name_plural': '試合形式'},
        ),
        migrations.AlterModelOptions(
            name='member',
            options={'verbose_name_plural': 'チーム人員'},
        ),
        migrations.AlterModelOptions(
            name='patterntype',
            options={'verbose_name_plural': '試合イベントパターン'},
        ),
        migrations.AlterModelOptions(
            name='playeronmatch',
            options={'verbose_name_plural': '試合登録プレイヤー'},
        ),
        migrations.AlterModelOptions(
            name='playerposition',
            options={'verbose_name_plural': 'ポジション'},
        ),
        migrations.AlterModelOptions(
            name='playerprofile',
            options={'verbose_name_plural': '選手プロフィール'},
        ),
        migrations.AlterModelOptions(
            name='scoringmethod',
            options={'verbose_name_plural': '得点手法'},
        ),
        migrations.AlterModelOptions(
            name='staffonmatch',
            options={'verbose_name_plural': '試合参加スタッフ'},
        ),
        migrations.AlterModelOptions(
            name='staffposition',
            options={'verbose_name_plural': '役職'},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'verbose_name_plural': 'チーム'},
        ),
        migrations.AlterModelOptions(
            name='teamgroup',
            options={'verbose_name_plural': 'チームグループ'},
        ),
        migrations.AlterModelOptions(
            name='teamonmatch',
            options={'verbose_name_plural': '試合参加チーム'},
        ),
        migrations.AlterField(
            model_name='half',
            name='number',
            field=models.IntegerField(verbose_name='序数'),
        ),
    ]
