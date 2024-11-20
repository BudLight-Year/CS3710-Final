from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from django.urls import reverse
from selenium.webdriver.common.action_chains import ActionChains
from user.models import MyUser, Profile

class UserTests(StaticLiveServerTestCase):
    def setUp(self):
        edge_options = webdriver.EdgeOptions()
        #edge_options.add_argument('--headless')
        service = Service(EdgeChromiumDriverManager().install())
        self.driver = webdriver.Edge(service=service, options=edge_options)
        
        # Create test user for selenium tests
        self.test_user = MyUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        Profile.objects.create(
            user=self.test_user,
            description='Test profile description'
        )

    def tearDown(self):
        self.driver.quit()

    def wait_and_get_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def test_signup(self):
        """Test signup functionality"""
        try:
            initial_user_count = MyUser.objects.count()
            
            # Navigate to signup page
            self.driver.get(self.live_server_url + '/user/signup/')
            
            # Assert we're on the signup page
            self.assertIn('Sign Up', self.driver.page_source)
            
            # Find form fields
            email_input = self.wait_and_get_element(By.ID, 'id_email')
            username_input = self.wait_and_get_element(By.ID, 'id_username')
            description_input = self.wait_and_get_element(By.ID, 'id_description')
            password1_input = self.wait_and_get_element(By.ID, 'id_password1')
            password2_input = self.wait_and_get_element(By.ID, 'id_password2')
            
            # Fill in the form
            test_email = 'newuser@example.com'
            test_username = 'newuser'
            test_description = 'Test description'
            
            email_input.send_keys(test_email)
            username_input.send_keys(test_username)
            description_input.send_keys(test_description)
            password1_input.send_keys('newpass123')
            password2_input.send_keys('newpass123')
            
            # Find and click submit button
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for redirect or success
            WebDriverWait(self.driver, 10).until(
                lambda driver: '/user/signup/' not in driver.current_url
            )
            
            # Verify user was created
            self.assertEqual(MyUser.objects.count(), initial_user_count + 1)
            
            # Get the new user and verify details
            new_user = MyUser.objects.get(email=test_email)
            self.assertEqual(new_user.username, test_username)
            
            # Verify profile was created
            profile = Profile.objects.get(user=new_user)
            self.assertEqual(profile.description, test_description)
            
            # Verify we can login with the new account
            self.assertTrue(new_user.check_password('newpass123'))
            
        except Exception as e:
            print(f"\nError in test_signup: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_login(self):
        """Test login functionality"""
        try:
            self.driver.get(self.live_server_url + '/user/login/')
            
            # Assert we're on the login page
            self.assertIn('Login', self.driver.title.title())
            
            # Find and fill form fields
            email_input = self.wait_and_get_element(By.NAME, 'login')
            password_input = self.wait_and_get_element(By.NAME, 'password')
            
            email_input.send_keys('test@example.com')
            password_input.send_keys('testpass123')
            
            # Find and click submit button
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for redirect
            WebDriverWait(self.driver, 10).until(
                lambda driver: '/user/login/' not in driver.current_url
            )
            
            # Verify we're logged in
            self.wait_and_get_element(By.CLASS_NAME, 'navbar-nav')
            self.assertIn(self.test_user.username, self.driver.page_source)
            self.assertNotIn('Login', self.driver.page_source)
            self.assertNotIn('Sign Up', self.driver.page_source)
            
            # Check profile access
            self.driver.get(self.live_server_url + '/user/profile/' + self.test_user.username)
            self.assertIn('Profile', self.driver.page_source)
            self.assertIn(self.test_user.username, self.driver.page_source)
            
        except Exception as e:
            print(f"\nError in test_login: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise

    def test_failed_login(self):
        """Test login with incorrect credentials"""
        try:
            self.driver.get(self.live_server_url + '/user/login/')
            
            email_input = self.wait_and_get_element(By.NAME, 'login')
            password_input = self.wait_and_get_element(By.NAME, 'password')
            
            # Try wrong password
            email_input.send_keys('test@example.com')
            password_input.send_keys('wrongpassword')
            
            submit_button = self.wait_and_get_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for and verify error message in the errorlist
            error_list = self.wait_and_get_element(By.CLASS_NAME, 'errorlist')
            self.assertIn('the email address and/or password you specified are not correct', 
                        error_list.text.lower())
            
            # Verify we're still on a login page
            self.assertIn('sign in', self.driver.page_source.lower())
            
        except Exception as e:
            print(f"\nError in test_failed_login: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            raise
