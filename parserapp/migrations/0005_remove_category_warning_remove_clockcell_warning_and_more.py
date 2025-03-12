# Generated by Django 5.1.6 on 2025-03-12 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parserapp', '0004_category_warning_category_warning_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='warning',
        ),
        migrations.RemoveField(
            model_name='clockcell',
            name='warning',
        ),
        migrations.RemoveField(
            model_name='disipline',
            name='warning',
        ),
        migrations.RemoveField(
            model_name='module',
            name='warning',
        ),
        migrations.RemoveField(
            model_name='studycycle',
            name='warning',
        ),
        migrations.RemoveField(
            model_name='studyplan',
            name='warning',
        ),
        migrations.AddField(
            model_name='category',
            name='warnings',
            field=models.BooleanField(default=False, verbose_name='Наличие предупреждений'),
        ),
        migrations.AddField(
            model_name='clockcell',
            name='warnings',
            field=models.BooleanField(default=False, verbose_name='Наличие предупреждений'),
        ),
        migrations.AddField(
            model_name='studycycle',
            name='warnings',
            field=models.BooleanField(default=False, verbose_name='Наличие предупреждений'),
        ),
        migrations.AddField(
            model_name='studyplan',
            name='warnings',
            field=models.BooleanField(default=False, verbose_name='Наличие предупреждений'),
        ),
        migrations.AlterField(
            model_name='category',
            name='warning_description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание предупреждений'),
        ),
        migrations.AlterField(
            model_name='clockcell',
            name='warning_description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание предупреждений'),
        ),
        migrations.AlterField(
            model_name='studycycle',
            name='warning_description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание предупреждений'),
        ),
        migrations.AlterField(
            model_name='studyplan',
            name='warning_description',
            field=models.TextField(blank=True, null=True, verbose_name='Описание предупреждений'),
        ),
    ]
