# Generated by Django 4.2 on 2024-09-01 19:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('torrents', '0006_remove_movie_mdblist_id_alter_movie_mediatype_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='mdblist_id',
        ),
    ]
