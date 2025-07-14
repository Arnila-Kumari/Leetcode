# LeetCode Login Automation

This project automates the login process for LeetCode using Selenium WebDriver. It provides a simple way to log in to LeetCode with either default credentials or user-provided ones.

## Features

- Automated login to LeetCode
- Support for default credentials
- Configurable browser settings
- Detailed logging
- Error handling and verification

## Requirements

- Python 3.6+
- Selenium
- webdriver-manager

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
python3 -m pip install selenium webdriver-manager
```

## Configuration

You can modify the `config.py` file to change:

- Default credentials
- Timeout settings
- Browser options
- Login URL

## Usage

Run the script with:

```bash
python3 main.py
```

When prompted:
- Press Enter to use default credentials
- Or enter your own credentials

## Project Structure

- `main.py`: Main script with login functionality
- `config.py`: Configuration settings
- `leetcode_login.log`: Log file (created when the script runs)

## Code Organization

The code is organized into several functions:

- `get_credentials()`: Handles user input for credentials
- `initialize_driver()`: Sets up the WebDriver with proper configuration
- `leetcode_login()`: Main function orchestrating the login process
- `perform_login()`: Handles the actual login form submission
- `verify_login_status()`: Verifies if login was successful

## Error Handling

The script includes comprehensive error handling for:

- Timeouts
- Missing elements
- Login failures
- Unexpected errors

## License

This project is available for personal and educational use.