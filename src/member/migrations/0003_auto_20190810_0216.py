# Generated by Django 2.2 on 2019-08-09 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('member', '0002_auto_20190810_0213')]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='staff_position',
            field=models.ManyToManyField(to='master.StaffPosition', verbose_name='役職'),
        )
    ]
