# Generated by Django 4.2 on 2024-08-29 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('torrents', '0004_alter_movie_tmdb_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='mdblist_id',
            field=models.IntegerField(blank=True),
        ),
    ]
