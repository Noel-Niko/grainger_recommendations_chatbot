import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Get the Chrome binary path from environment variable
chrome_binary_path = os.getenv('CHROME_BINARY_PATH')
options = Options()
options.binary_location = chrome_binary_path

try:
    # Set the path to ChromeDriver
    service = Service('/usr/local/bin/chromedriver')

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    # Open a webpage to test
    driver.get("http://www.google.com")

    print(f"Using Chrome binary at: {chrome_binary_path}")
    print("ChromeDriver initialized successfully.")

    # Close the browser
    driver.quit()
except Exception as e:
    print(f"Error initializing ChromeDriver: {e}")
