from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import activate
from django.test import TestCase

from .models import Word, WordTranslation

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