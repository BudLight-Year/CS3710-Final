from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from django.urls import reverse
from user.models import MyUser, Profile
from recommendations.models import Movie, Recommendation, Preference
import time
import requests



class RecommendationTests(StaticLiveServerTestCase):
    def setUp(self):
        edge_options = webdriver.EdgeOptions()
        # edge_options.add_argument('--headless')  # Uncomment to run tests in headless mode
        service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=edge_options)
        
        # Create test users
        self.user1 = MyUser.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = MyUser.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        Profile.objects.create(user=self.user1, description='User 1 profile description')
        Profile.objects.create(user=self.user2, description='User 2 profile description')
        
        # Create movies
        movies = [
            Movie.objects.create(movie_id=1, title='Movie 1', genres='Action', mean=7.5, count=100),
            Movie.objects.create(movie_id=2, title='Movie 2', genres='Comedy', mean=6.0, count=150),
            Movie.objects.create(movie_id=3, title='Movie 3', genres='Drama', mean=8.0, count=200),
            Movie.objects.create(movie_id=4, title='Movie 4', genres='Action', mean=5.5, count=50),
            Movie.objects.create(movie_id=5, title='Movie 5', genres='Comedy', mean=6.5, count=120),
            Movie.objects.create(movie_id=6, title='Movie 6', genres='Drama', mean=7.0, count=90),
            Movie.objects.create(movie_id=7, title='Movie 7', genres='Action', mean=8.5, count=300),
            Movie.objects.create(movie_id=8, title='Movie 8', genres='Comedy', mean=7.2, count=110),
            Movie.objects.create(movie_id=9, title='Movie 9', genres='Drama', mean=9.0, count=80),
            Movie.objects.create(movie_id=10, title='Movie 10', genres='Action', mean=6.8, count=160)
        ]
        
        # Create preferences
        preferences = [
            Preference.objects.create(genre1='Action', include_other_genres=True),
            Preference.objects.create(genre1='Comedy', include_other_genres=True)
        ]
        
        # Create recommendations
        for i in range(5):
            recommendation1 = Recommendation.objects.create(user=self.user1, preference=preferences[0])
            recommendation1.movies.add(*movies[:5])
            
            recommendation2 = Recommendation.objects.create(user=self.user2, preference=preferences[1])
            recommendation2.movies.add(*movies[5:])

        # Log in the test user using Selenium
        self.driver.get(self.live_server_url + reverse('user:account_login'))
        email_input = self.wait_and_get_element(By.NAME, 'login')
        password_input = self.wait_and_get_element(By.NAME, 'password')
        email_input.send_keys('user1@example.com')
        password_input.send_keys('testpass123')
        submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
        self.driver.execute_script("arguments[0].click();", submit_button)

    def tearDown(self):
        self.driver.quit()

    def wait_and_get_element(self, by, value, timeout=20):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def test_recommendation_creation(self):
        """Test the creation of a recommendation based on user preferences"""
        try:
            # Navigate to recommendation engine page
            self.driver.get(self.live_server_url + reverse('recommendations:engine'))
            print(f"Navigated to: {self.driver.current_url}")
            
            # Assert we're on the recommendation engine page
            self.assertIn('Recommendation Engine', self.driver.page_source)
            
            # Find and fill the form fields
            genre1_input = self.wait_and_get_element(By.ID, 'id_genre1')
            genre2_input = self.wait_and_get_element(By.ID, 'id_genre2')
            include_other_genres_checkbox = self.wait_and_get_element(By.ID, 'id_include_other_genres')
            
            genre1_input.send_keys('Action')
            genre2_input.send_keys('Adventure')
            include_other_genres_checkbox.click()
            
            # Find and click submit button
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for page to load and check for specific content
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Recommendation for user1')]"))
            )
            print(f"Redirected to: {self.driver.current_url}")
            
            # Additional wait to ensure the page content is loaded
            time.sleep(5)
            
            # Capture screenshot for debugging
            #self.driver.save_screenshot('recommendation_detail_page.png')
            
            # Log page source for debugging
            #print(f"Page source after redirect:\n{self.driver.page_source}")
            
            # Verify the recommendation was created
            recommendation = Recommendation.objects.filter(user=self.user1).first()
            self.assertIsNotNone(recommendation)
            print(f"Recommendation created: {recommendation}")
            
            # Verify the recommendation details page
            self.assertIn('Recommendation for user1', self.driver.page_source)
            self.assertIn('How was this recommendation?', self.driver.page_source)
            
        except Exception as e:
            print(f"\nError in test_recommendation_creation: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_recommendation_creation_with_no_preferences(self):
        """Test the creation of a recommendation with no preferences, which should trigger a form error"""
        try:
            # Navigate to recommendation engine page
            self.driver.get(self.live_server_url + reverse('recommendations:engine'))
            print(f"Navigated to: {self.driver.current_url}")
            
            # Assert we're on the recommendation engine page
            self.assertIn('Recommendation Engine', self.driver.page_source)
            
            # Submit the form without filling in any preferences
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for the page to reload and check for form error
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.errorlist'))
            )
            print(f"Form reloaded with error: {self.driver.current_url}")
            
            # Log page source for debugging
            #print(f"Page source after form submission:\n{self.driver.page_source}")
            
            # Verify the form error message
            self.assertIn('Please select at least one genre in any of the fields.', self.driver.page_source)
            
        except Exception as e:
            print(f"\nError in test_recommendation_creation_with_no_preferences: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise



    def test_recommendation_detail_view(self):
        """Test viewing the details of a recommendation and submitting feedback"""
        try:
            # Create test recommendation
            movie = Movie.objects.create(movie_id=11, title='Test Movie', genres='Action', mean=7.5, count=100)
            preference = Preference.objects.create(genre1='Action', include_other_genres=True)
            recommendation = Recommendation.objects.create(user=self.user1, preference=preference)
            recommendation.movies.add(movie)
            
            # Navigate to recommendation detail page
            self.driver.get(self.live_server_url + reverse('recommendations:recommendation_detail', kwargs={'recommendation_id': recommendation.id}))
            
            # Assert we're on the recommendation detail page
            self.assertIn('Recommendation for user1', self.driver.page_source)
            self.assertIn('How was this recommendation?', self.driver.page_source)
            
            # Submit feedback
            good_feedback_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[name="feedback"][value="True"]')
            self.driver.execute_script("arguments[0].click();", good_feedback_button)
            
            # Verify thank-you message
            self.assertIn('Thank you for your feedback!', self.driver.page_source)
            
        except Exception as e:
            print(f"\nError in test_recommendation_detail_view: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_recommendations_list_view(self):
        """Test viewing the list of recommendations"""
        try:
            # Navigate to recommendations list page
            self.driver.get(self.live_server_url + reverse('recommendations:recommendations_list'))
            
            # Assert we're on the recommendations list page
            self.assertIn('All Recommendations', self.driver.page_source)
            self.assertIn('Movie 1', self.driver.page_source)
            self.assertIn('Movie 2', self.driver.page_source)
            
        except Exception as e:
            print(f"\nError in test_recommendations_list_view: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_create_and_delete_recommendation(self):
        """Test creating and deleting a recommendation"""
        try:
            # Navigate to recommendation engine page
            self.driver.get(self.live_server_url + reverse('recommendations:engine'))
            print(f"Navigated to: {self.driver.current_url}")
            
            # Assert we're on the recommendation engine page
            self.assertIn('Recommendation Engine', self.driver.page_source)
            
            # Find and fill the form fields
            genre1_input = self.wait_and_get_element(By.ID, 'id_genre1')
            genre2_input = self.wait_and_get_element(By.ID, 'id_genre2')
            include_other_genres_checkbox = self.wait_and_get_element(By.ID, 'id_include_other_genres')
            
            genre1_input.send_keys('Action')
            genre2_input.send_keys('Adventure')
            include_other_genres_checkbox.click()
            
            # Find and click submit button
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for redirect and verify page content
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Recommendation for user1')]"))
            )
            print(f"Redirected to: {self.driver.current_url}")
            
            # Verify the recommendation was created
            recommendation = Recommendation.objects.filter(user=self.user1).first()
            self.assertIsNotNone(recommendation)
            print(f"Recommendation created: {recommendation}")
            
            # Navigate to the user's profile page
            self.driver.get(self.live_server_url + reverse('user:profile', kwargs={'username': self.user1.username}))
            self.assertIn(f"{self.user1.username}'s Profile", self.driver.page_source)
            
            # Find and click the delete button for the created recommendation
            delete_modal_button = self.wait_and_get_element(By.CSS_SELECTOR, f'button[data-bs-target="#deleteModal{recommendation.id}"]')
            self.driver.execute_script("arguments[0].click();", delete_modal_button)
            
            # Wait for the modal to appear
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, f'deleteModal{recommendation.id}'))
            )
            
            # Log page source before confirming deletion
            print(f"Page source before confirming deletion:\n{self.driver.page_source}")
            
            # Find and click the confirm delete button within the modal
            confirm_delete_button = self.wait_and_get_element(By.CSS_SELECTOR, f'a[href="{reverse("recommendations:delete_recommendation", kwargs={"recommendation_id": recommendation.id})}"]')
            self.driver.execute_script("arguments[0].click();", confirm_delete_button)
            
            # Wait for redirect back to profile page and verify the recommendation is deleted
            WebDriverWait(self.driver, 30).until(
                lambda driver: f'/user/profile/{self.user1.username}/' in driver.current_url
            )
            print(f"Redirected to profile page: {self.driver.current_url}")
            
            # Verify the recommendation was deleted
            deleted_recommendation = Recommendation.objects.filter(id=recommendation.id).first()
            self.assertIsNone(deleted_recommendation)
            print("Recommendation deleted successfully")
            
        except Exception as e:
            print(f"\nError in test_create_and_delete_recommendation: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise


    def test_delete_nonexistent_recommendation(self):
        """Test attempting to delete a non-existent recommendation"""
        try:
            # Ensure the user is logged in from setUp
            print(f"User {self.user1.username} logged in successfully.")
            
            # Construct the URL for a non-existent recommendation
            nonexistent_id = 9999
            delete_url = self.live_server_url + reverse('recommendations:delete_recommendation', kwargs={'recommendation_id': nonexistent_id})
            
            # Navigate to the delete URL using Selenium
            self.driver.get(delete_url)
            print(f"Navigated to delete URL: {delete_url}")
            
            # Wait for the "Not found" page to be displayed
            WebDriverWait(self.driver, 10).until(
                lambda driver: 'Not Found' in driver.page_source or 'Not found' in driver.page_source
            )
            
            # Verify the "Not Found" message
            self.assertIn('Not Found', self.driver.page_source)
            print("Not found message displayed for non-existent recommendation")
            
        except Exception as e:
            print(f"\nError in test_delete_nonexistent_recommendation: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_access_recommendation_creation_not_logged_in(self):
        """Test accessing the recommendation creation page while not logged in"""
        try:
            # Log out the user using Selenium
            self.driver.get(self.live_server_url + reverse('user:account_logout'))
            print("Navigated to logout URL")

            # Clear cookies to ensure the session is invalidated
            self.driver.delete_all_cookies()
            print("Cleared cookies to invalidate session")

            # Try to navigate to the recommendation engine page
            self.driver.get(self.live_server_url + reverse('recommendations:engine'))
            print("Navigated to recommendation engine page URL")
            
            # Wait for the redirect to the login page
            WebDriverWait(self.driver, 30).until(
                lambda driver: 'login' in driver.current_url
            )
            print(f"Redirected to login page: {self.driver.current_url}")
            
            # Verify the user is redirected to the login page
            self.assertIn('Login', self.driver.page_source)
            print("Login page displayed successfully")
            
        except Exception as e:
            print(f"\nError in test_access_recommendation_creation_not_logged_in: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise



