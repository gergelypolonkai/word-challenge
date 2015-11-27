# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings

def migrate_words(apps, schema_editor):
    Word = apps.get_model('words', 'Word')
    WordTranslation = apps.get_model('words', 'WordTranslation')

    for translation in WordTranslation.objects.all(): # pragma: no cover
        word = translation.word
        if word.word is not None:
            word = Word.objects.create()

        word.word = translation.word
        word.language = translation.language
        word.added_by = translation.added_by
        word.added_at = translation.added_at
        word.save()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('words', '0004_work_upload_time'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='wordtranslation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='wordtranslation',
            name='added_by',
        ),
        migrations.RemoveField(
            model_name='wordtranslation',
            name='word',
        ),
        migrations.AddField(
            model_name='word',
            name='added_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='word',
            name='added_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='word',
            name='language',
            field=models.CharField(null=True, max_length=5),
        ),
        migrations.AddField(
            model_name='word',
            name='word',
            field=models.CharField(null=True, max_length=100),
        ),
        migrations.RunPython(migrate_words),
        migrations.AlterUniqueTogether(
            name='word',
            unique_together=set([('language', 'word')]),
        ),
        migrations.DeleteModel(
            name='WordTranslation',
        ),
        migrations.AlterField(
            model_name='word',
            name='added_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='word',
            name='language',
            field=models.CharField(max_length=5),
        ),
        migrations.AlterField(
            model_name='word',
            name='word',
            field=models.CharField(max_length=100),
        ),
    ]
