import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# 1. Global or Persistent Driver Setup
def get_driver(width=1920, height=1080, scale=2):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--window-size={width},{height}")
    chrome_options.add_argument(f"--force-device-scale-factor={scale}")

    # This checks cache first, then installs ONLY if missing/outdated
    driver_path = ChromeDriverManager().install()
    return webdriver.Chrome(service=Service(driver_path), options=chrome_options)


# 2. Optimized Function (Uses an existing driver)
def capture_screen(
    driver,
    html_filepath: str,
) -> bytes:
    abs_path = os.path.abspath(html_filepath)
    driver.get(f"file://{abs_path}")

    # Wait for tiles
    time.sleep(2)

    # Return screenshot as PNG binary instead of saving to file
    screenshot_bytes = driver.get_screenshot_as_png()
    return screenshot_bytes
