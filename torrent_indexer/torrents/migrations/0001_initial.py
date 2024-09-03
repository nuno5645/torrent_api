# Generated by Django 5.1 on 2024-08-25 17:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StreamingList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mdblist_id', models.IntegerField(unique=True)),
                ('tmdb_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('imdb_id', models.CharField(max_length=20, unique=True)),
                ('tvdbid', models.IntegerField(blank=True, null=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('overview', models.TextField(blank=True, null=True)),
                ('rank', models.IntegerField(blank=True, null=True)),
                ('adult', models.BooleanField(default=False)),
                ('mediatype', models.CharField(max_length=10)),
                ('release_year', models.IntegerField()),
                ('poster_path', models.CharField(blank=True, max_length=255, null=True)),
                ('backdrop_path', models.CharField(blank=True, max_length=255, null=True)),
                ('vote_average', models.FloatField(blank=True, null=True)),
                ('vote_count', models.IntegerField(blank=True, null=True)),
                ('popularity', models.FloatField(blank=True, null=True)),
                ('streaming_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movies', to='torrents.streaminglist')),
            ],
        ),
        migrations.CreateModel(
            name='Torrent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('magnet_link', models.TextField()),
                ('file_size', models.BigIntegerField()),
                ('seeders', models.IntegerField()),
                ('leechers', models.IntegerField()),
                ('upload_date', models.DateTimeField()),
                ('quality', models.CharField(max_length=10)),
                ('resolution', models.CharField(max_length=10)),
                ('codec', models.CharField(max_length=10)),
                ('audio_codec', models.CharField(max_length=10)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='torrents', to='torrents.movie')),
            ],
        ),
        migrations.CreateModel(
            name='RealDebrid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rd_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(max_length=50)),
                ('download_link', models.URLField(max_length=500)),
                ('added_date', models.DateTimeField(auto_now_add=True)),
                ('last_checked', models.DateTimeField(auto_now=True)),
                ('file_path', models.CharField(max_length=500)),
                ('file_size', models.BigIntegerField()),
                ('seeders', models.IntegerField()),
                ('speed', models.CharField(max_length=50)),
                ('progress', models.FloatField(default=0)),
                ('torrent', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='real_debrid', to='torrents.torrent')),
            ],
        ),
    ]