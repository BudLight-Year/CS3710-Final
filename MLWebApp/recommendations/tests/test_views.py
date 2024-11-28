from django.test import TestCase
from django.urls import reverse
from recommendations.models import Recommendation, Movie, Preference, Feedback
from user.models import MyUser


class RecommendationEngineViewTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', email="test@test.com", password='12345')
        self.client.login(email='test@test.com', password='12345')

        # Create some movie instances
        Movie.objects.create(movie_id=1, title='Inception', genres='Action,Sci-Fi', mean=8.8, count=1000)
        Movie.objects.create(movie_id=2, title='Interstellar', genres='Adventure,Drama', mean=8.6, count=900)

    def test_get_recommendation_engine(self):
        response = self.client.get(reverse('recommendations:engine'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recommendations/recommendation_engine.html')

    def test_post_recommendation_engine_valid(self):
        preference_data = {
            'genre1': 'Action',
            'genre2': 'Sci-Fi',
            'include_other_genres': True
        }
        response = self.client.post(reverse('recommendations:engine'), data=preference_data)
        self.assertEqual(response.status_code, 302)


class RecommendationDetailViewTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', email='test@test.com', password='12345')
        self.preference = Preference.objects.create(genre1='Action')
        self.recommendation = Recommendation.objects.create(user=self.user, preference=self.preference)
        self.client.login(email='test@test.com', password='12345')

        # Create some movie instances
        Movie.objects.create(movie_id=1, title='Inception', genres='Action,Sci-Fi', mean=8.8, count=1000)
        Movie.objects.create(movie_id=2, title='Interstellar', genres='Adventure,Drama', mean=8.6, count=900)

    def test_get_recommendation_detail(self):
        response = self.client.get(reverse('recommendations:recommendation_detail', args=[self.recommendation.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recommendations/recommendation_detail.html')

    def test_post_feedback_valid(self):
        feedback_data = {'feedback': True}
        response = self.client.post(reverse('recommendations:recommendation_detail', args=[self.recommendation.id]), data=feedback_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you for your feedback!')


class RecommendationsListViewTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', email='test@test.com', password='12345')
        self.client.login(email='test@test.com', password='12345')

        # Create some movie instances
        Movie.objects.create(movie_id=1, title='Inception', genres='Action,Sci-Fi', mean=8.8, count=1000)
        Movie.objects.create(movie_id=2, title='Interstellar', genres='Adventure,Drama', mean=8.6, count=900)

    def test_get_recommendations_list(self):
        response = self.client.get(reverse('recommendations:recommendations_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'recommendations/recommendation_list.html')


class DeleteRecommendationViewTest(TestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(username='testuser', email='test@test.com', password='12345')
        self.preference = Preference.objects.create(genre1='Action')
        self.recommendation = Recommendation.objects.create(user=self.user, preference=self.preference)
        self.client.login(email='test@test.com', password='12345')

        # Create some movie instances
        Movie.objects.create(movie_id=1, title='Inception', genres='Action,Sci-Fi', mean=8.8, count=1000)
        Movie.objects.create(movie_id=2, title='Interstellar', genres='Adventure,Drama', mean=8.6, count=900)

    def test_delete_recommendation(self):
        response = self.client.post(reverse('recommendations:delete_recommendation', args=[self.recommendation.id]))
        self.assertRedirects(response, reverse('user:profile', args=[self.user.username]))
