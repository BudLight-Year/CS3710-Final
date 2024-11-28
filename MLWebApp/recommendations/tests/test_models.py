from django.test import TestCase
from recommendations.models import Movie, Preference, Recommendation, Feedback
from user.models import MyUser
from django.utils import timezone


class MovieModelTest(TestCase):

    def test_movie_str(self):
        movie = Movie.objects.create(movie_id=1, title='Inception', genres='Action,Sci-Fi')
        self.assertEqual(str(movie), 'Inception')


class PreferenceModelTest(TestCase):

    def test_preference_str(self):
        preference = Preference.objects.create(genre1='Action', genre2='Sci-Fi')
        self.assertEqual(str(preference), 'Preference: Action, Sci-Fi')


class RecommendationModelTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create(username='testuser')
        self.preference = Preference.objects.create(genre1='Action', genre2='Sci-Fi')
        self.recommendation = Recommendation.objects.create(user=self.user, preference=self.preference)

    def test_recommendation_str(self):
        self.assertEqual(str(self.recommendation), f"Recommendation for {self.user.username}")


class FeedbackModelTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create(username='testuser', email='test@test.com')
        self.preference = Preference.objects.create(genre1='Action', genre2='Sci-Fi')
        self.recommendation = Recommendation.objects.create(user=self.user, preference=self.preference)
        self.feedback = Feedback.objects.create(feedback=True, recommendation=self.recommendation)

    def test_feedback_creation(self):
        self.assertTrue(self.feedback.feedback)
        self.assertEqual(self.feedback.recommendation, self.recommendation)
