# Generated by Django 4.2 on 2024-08-26 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('torrents', '0002_remove_movie_slug_remove_movie_streaming_list_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='imdb_id',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]