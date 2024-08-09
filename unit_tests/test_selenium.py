import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestBedrockClientManager(unittest.TestCase):
    def test_access_chrome_driver(self):
        result = False
        try:
            # Set the path to ChromeDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  # Example option for headless mode

            # Automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())

            # Initialize the Chrome WebDriver
            driver = webdriver.Chrome(service=service, options=options)

            # Open a webpage to test
            driver.get("http://www.google.com")

            print(f"Using Chrome binary at: {chrome_binary_path}")
            print("ChromeDriver initialized successfully.")
            result = True
            # Close the browser
            driver.quit()
        except Exception as e:
            print(f"Error initializing ChromeDriver: {e}")

        self.assertTrue(result, msg="ChromeDriver initialization failed.")
