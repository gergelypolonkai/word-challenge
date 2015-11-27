from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_duration
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import get_language

@python_2_unicode_compatible
class Word(models.Model):
    language = models.CharField(max_length=5)
    word = models.CharField(max_length=100, null=False, blank=False)
    added_by = models.ForeignKey(User)
    added_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.word

    def __repr__(self):
        return '<Word: {} ({})>'.format(self.word, self.language)

    class Meta:
        unique_together = (('language', 'word'),)

class Draw(models.Model):
    user = models.ForeignKey(User)
    word = models.ForeignKey(Word, related_name='draws')
    accepted = models.NullBooleanField()
    timestamp = models.DateTimeField(default=timezone.now)

    def successful(self):
        max_duration = parse_duration(settings.DRAW_TIME)

        try:
            work = self.work
        except Work.DoesNotExist:
            work = None

        if work is None:
            elapsed_time = timezone.now() - self.timestamp

            if elapsed_time >= max_duration:
                return False

            return None

        if self.work.upload_time - self.timestamp > max_duration:
            return False

        return True

    class Meta:
        ordering = ('timestamp',)

class Work(models.Model):
    draw = models.OneToOneField(Draw, related_name='work', primary_key=True)
    language = models.CharField(max_length=5, db_index=True)
    upload_time = models.DateTimeField(default=timezone.now)
