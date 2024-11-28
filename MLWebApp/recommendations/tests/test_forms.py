from django.test import TestCase
from recommendations.forms import PreferenceForm, FeedbackForm
from recommendations.models import Preference


class PreferenceFormTest(TestCase):

    def test_valid_preference_form(self):
        form = PreferenceForm(data={
            'genre1': 'Action',
            'genre2': 'Sci-Fi',
            'include_other_genres': True
        })
        self.assertTrue(form.is_valid())

    def test_invalid_preference_form(self):
        form = PreferenceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['__all__'], ['Please select at least one genre in any of the fields.'])


class FeedbackFormTest(TestCase):

    def test_valid_feedback_form(self):
        form = FeedbackForm(data={'feedback': True})
        self.assertTrue(form.is_valid())

    def test_invalid_feedback_form(self):
        form = FeedbackForm(data={})
        self.assertFalse(form.is_valid())
