# Generated by Django 5.0.6 on 2024-11-17 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommendations', '0002_alter_preference_genre1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='movie',
            name='mean',
            field=models.FloatField(default=0),
        ),
    ]
