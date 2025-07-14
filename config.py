# Configuration file for LeetCode login script

# Default credentials
DEFAULT_USERNAME = "fast_and_furious"
DEFAULT_PASSWORD = "Roksakotohr0kl0"

# Timeout settings (in seconds)
PAGE_LOAD_TIMEOUT = 15
IMPLICIT_WAIT = 10
MAX_LOGIN_ATTEMPTS = 4000
# URLs
LOGIN_URL = "https://leetcode.com/accounts/login/"
LOGIN_CHECK_INTERVAL = 1
# Browser settings
BROWSER_OPTIONS = [
    "--start-maximized",  # Start with maximized browser
    # Add more Chrome options as needed
    # "--headless",  # Uncomment to run in headless mode
    # "--disable-gpu",
    # "--no-sandbox",
]
