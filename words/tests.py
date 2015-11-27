# -*- coding: utf-8
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_duration
from django.utils.translation import activate
from django.test import TestCase, override_settings

from .models import Word, WordTranslation, Draw, Work

class WordTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='test', password='test')
        self.word1 = Word.objects.create()
        self.translation1 = WordTranslation.objects.create(
            word=self.word1,
            language='en-us',
            translation='color',
            added_by=user)
        self.translation2 = WordTranslation.objects.create(
            word=self.word1,
            language='en-gb',
            translation='colour',
            added_by=user)
        self.translation3 = WordTranslation.objects.create(
            word=self.word1,
            language='hu-hu',
            translation='szín',
            added_by=user)

    def test_word_str(self):
        with self.settings(LANGUAGE_CODE='en-us'):
            self.assertEquals("color", self.word1.__str__())

        with self.settings(LANGUAGE_CODE='en-gb'):
            self.assertEquals('colour', self.word1.__str__())

        activate('hu-hu')
        self.assertEquals('szín', self.word1.__str__())

        with self.settings(LANGUAGE_CODE='es-es'):
            activate('is-is')
            self.assertEquals('', self.word1.__str__())

    def test_word_translation(self):
        self.assertEquals('color', self.word1.translation('en-us').translation)
        self.assertEquals('colour', self.word1.translation('en-gb').translation)
        self.assertIsNone(self.word1.translation('is-is'))

    def test_translation_validation(self):
        word = WordTranslation()

        with self.assertRaises(ValidationError) as ctx:
            word.clean()

        self.assertEquals('translation-empty', ctx.exception.code)

    def test_translation_str(self):
        self.assertEquals('color', self.translation1.__str__())

@override_settings(DRAW_TIME='1 00:00:00')
class DrawTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.word = Word.objects.create()

    def test_current_word(self):
        self.assertIsNone(self.user.current_word())

        draw = Draw.objects.create(user=self.user,
                                   word=self.word,
                                   accepted=None)
        self.assertEquals(self.word, self.user.current_word())

        draw.accepted = True
        draw.save()
        self.assertEquals(self.word, self.user.current_word())

    def test_draw_word(self):
        # User has no words yet
        self.assertEquals(self.word, self.user.draw_word())

        # User now has an unaccepted draw
        self.assertEquals(self.word, self.user.draw_word())

        # Accept the last word and make it appear as if it would be 2
        # days ago
        draw = Draw.objects.get(user=self.user, word=self.word)
        draw.accepted = True
        draw.timestamp -= timedelta(days=2)
        draw.save()
        Work.objects.create(draw=draw)

        # Create a second word for further testing
        word2 = Word.objects.create()

        # The next word should be different from the previous one
        self.assertEquals(word2, self.user.draw_word())

        # The new word should not be accepted (as it is a new draw)
        draw = Draw.objects.get(user=self.user, word=word2)
        self.assertIsNotNone(draw)
        self.assertIsNone(draw.accepted)

        # Accept the word, make it old again, and create a work for it
        draw.accepted = True
        draw.timestamp -= timedelta(days=2)
        draw.save()
        work = Work.objects.create(draw=draw)

        # As we are out of words now, a new draw should return None
        self.assertIsNone(self.user.draw_word())

        # Now set the last draw to fresh again, and remove the associated work.
        draw.timestamp = timezone.now()
        draw.save()
        work.delete()
        # Also create a new word
        word3 = Word.objects.create()

        # A next draw should return the same word in this case
        self.assertEquals(word2, self.user.draw_word())

        # Now let’s reject this draw and draw a new one
        draw = Draw.objects.get(user=self.user, word=word2)
        draw.accepted = False
        draw.save()

        # The next draw should be different from the last
        self.assertEquals(word3, self.user.draw_word())

        # Now make the previous one accepted and completed, and reject
        # this last one
        draw.accepted = True
        draw.save()
        Work.objects.create(draw=draw)

        draw = Draw.objects.get(user=self.user, word=word3)
        draw.accepted = False
        draw.save()

        # The next draw must be this last, rejected one (as there are
        # no other options)
        self.assertEquals(word3, self.user.draw_word())

    def test_last_draw(self):
        draw = Draw.objects.create(
            user=self.user,
            word=self.word,
            accepted=True,
            timestamp=timezone.now() - timedelta(days=1))
        Work.objects.create(draw=draw)
        word = Word.objects.create()
        draw = Draw.objects.create(user=self.user,
                            word=word,
                            accepted=True)
        Work.objects.create(draw=draw)

        self.assertEquals(word, self.user.last_draw().word)

    def test_draw_per_day(self):
        draw = Draw.objects.create(user=self.user,
                                   word=self.word,
                                   accepted=True)
        Work.objects.create(draw=draw)
        Word.objects.create()

        self.assertEquals(self.word, self.user.draw_word())

    def test_draw_successful(self):
        # If there is no work, but we are within the time range
        draw = Draw.objects.create(
            user=self.user,
            word=Word.objects.create(),
            accepted=True,
            timestamp=timezone.now())
        self.assertIsNone(draw.successful())

        # If there is no work and we are out of time
        draw.timestamp -= timedelta(days=2)
        draw.save()
        self.assertIsNotNone(draw.successful())
        self.assertFalse(draw.successful())

        # If there is work and it was submitted on time
        draw.timestamp = timezone.now() + timedelta(minutes=1)
        draw.save()
        Work.objects.create(draw=draw)
        self.assertTrue(draw.successful())

        # If there is work and it wasn’t submitted on time
        draw.timestamp = timezone.now() - timedelta(days=2)
        draw.save()
        self.assertIsNotNone(draw.successful())
        self.assertFalse(draw.successful())

    def test_failed_successful_words(self):
        self.assertEquals([], self.user.failed_words())

        draw = Draw.objects.create(user=self.user,
                                   word=self.word,
                                   accepted=True,
                                   timestamp=timezone.now() - timedelta(days=2))
        self.assertEquals([draw.word], self.user.failed_words())
        self.assertEquals([], self.user.successful_words())

        draw2 = Draw.objects.create(user=self.user,
                                   word=Word.objects.create(),
                                   accepted=True,
                                   timestamp=timezone.now() - timedelta(days=3))
        Work.objects.create(draw=draw2,
                            upload_time=timezone.now() - timedelta(days=3))

        self.assertEquals([draw.word], self.user.failed_words())
        self.assertEquals([draw2.word], self.user.successful_words())
