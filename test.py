import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def test_chrome():
    try:
        # Set up Chrome options
        print("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Use default ChromeDriver from system PATH
        print("Starting Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google
        print("Going to Google...")
        driver.get('https://www.google.com')
        
        # Wait for 5 seconds to see the page
        print("Waiting for 5 seconds...")
        time.sleep(5)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    finally:
        print("Closing browser...")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    test_chrome()