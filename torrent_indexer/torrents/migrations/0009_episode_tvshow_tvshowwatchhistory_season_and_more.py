# Generated by Django 4.2 on 2024-09-26 23:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('torrents', '0008_watchhistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('episode_number', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('still_path', models.CharField(blank=True, max_length=255, null=True)),
                ('air_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TVShow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdb_id', models.IntegerField(unique=True)),
                ('imdb_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('tvdb_id', models.IntegerField(blank=True, null=True)),
                ('title', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('poster_path', models.CharField(blank=True, max_length=255, null=True)),
                ('backdrop_path', models.CharField(blank=True, max_length=255, null=True)),
                ('first_air_date', models.DateField(blank=True, null=True)),
                ('vote_average', models.FloatField(blank=True, null=True)),
                ('vote_count', models.IntegerField(blank=True, null=True)),
                ('popularity', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TVShowWatchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('watched_at', models.DateTimeField(auto_now_add=True)),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='watch_history', to='torrents.episode')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tv_watch_history', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season_number', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('overview', models.TextField(blank=True, null=True)),
                ('poster_path', models.CharField(blank=True, max_length=255, null=True)),
                ('air_date', models.DateField(blank=True, null=True)),
                ('tv_show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='torrents.tvshow')),
            ],
            options={
                'unique_together': {('tv_show', 'season_number')},
            },
        ),
        migrations.AddField(
            model_name='episode',
            name='season',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='torrents.season'),
        ),
        migrations.AlterUniqueTogether(
            name='episode',
            unique_together={('season', 'episode_number')},
        ),
    ]
