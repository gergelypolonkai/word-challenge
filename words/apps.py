# -*- coding: utf-8
from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_duration

def _current_word(self):
    from .models import Draw

    # If the user has an undecided draw, return that one
    try:
        word = Draw.objects.get(user=self, accepted=None).word

        return word
    except Draw.DoesNotExist:
        pass

    # If the user has an accepted draw that is unfinished (ie. no work
    # is uploaded), return that one
    try:
        word = Draw.objects.get(user=self, accepted=True, work=None).word

        return word
    except Draw.DoesNotExist:
        pass

    return None

def _last_draw(self):
    from .models import Draw

    return Draw.objects.filter(user=self).order_by('-timestamp').first()

def _draw_word(self):
    if self.current_word() is not None:
        return self.current_word()

    from .models import Word, Draw

    last_draw = self.last_draw()
    duration = parse_duration(settings.DRAW_TIME)

    if last_draw is not None \
       and (last_draw.accepted is None
            or last_draw.accepted == True) \
       and last_draw.timestamp + duration > timezone.now():
        return last_draw.word

    # Find all words
    # Exclude all words that has an accepted draw for this user
    # Choose a random one
    # If there are no more words, return None
    if last_draw is not None:
        last_word = last_draw.word
    else:
        last_word = None

    all_words = Word.objects.exclude(draws__accepted=True, draws__user=self)
    all_count = all_words.count()

    # If there are no more words, return None
    if all_count == 0:
        return None

    # If there is only one word, return it, regardless if it’s the
    # same as the last one
    if all_count == 1:
        word = all_words.first()
    # Otherwise, choose a word different from the last one
    else:
        word = last_word

        while last_word == word:
            word = all_words.order_by('?').first()

    Draw.objects.create(user=self, word=word, accepted=None)

    return word

def _failed_words(self):
    from .models import Draw

    flt = filter(lambda x: not x.successful(), Draw.objects.filter(user=self))

    return [draw.word for draw in flt]

def _successful_words(self):
    from .models import Draw

    flt = filter(lambda x: x.successful(), Draw.objects.filter(user=self))

    return [draw.word for draw in flt]

class WordsConfig(AppConfig):
    name = 'words'

    def ready(self):
        User.current_word = _current_word
        User.draw_word = _draw_word
        User.last_draw = _last_draw
        User.failed_words = _failed_words
        User.successful_words = _successful_words
