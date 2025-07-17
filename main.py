#!/usr/bin/env python3
"""
LeetCode Login Automation Script

This script automates the login process for LeetCode using undetected-chromedriver.
It supports both single-account and multi-account modes with advanced anti-detection.

Features:
- Undetected Chrome browser to bypass Cloudflare protection
- Multi-account parallel processing to avoid rate limits
- Environment variable credential management for security
- Automatic problem submission and documentation
- State management for resuming sessions
- Comprehensive error handling

Credential Setup:
    Set LEET_CREDS environment variable:
    export LEET_CREDS='user1@example.com:pass1,user2@example.com:pass2'
    
    Or create a .env file:
    LEET_CREDS=user1@example.com:pass1,user2@example.com:pass2

Usage:
    python main.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import getpass
import time
import logging
import sys
import os
import json
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    # Check if .env file exists before loading
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file_path):
        load_dotenv()  # Load environment variables from .env file
        # Only show this if we actually have credentials in the .env file
        with open(env_file_path, 'r') as f:
            if 'LEET_CREDS=' in f.read():
                print("🔐 Loaded environment variables from .env file")
    else:
        load_dotenv()  # Still call load_dotenv in case there are other .env files
except ImportError:
    print("💡 Install python-dotenv for .env file support: pip install python-dotenv")

# Import configuration
from config import (
    DEFAULT_USERNAME, DEFAULT_PASSWORD, PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT, LOGIN_URL, BROWSER_OPTIONS, LOGIN_CHECK_INTERVAL,
    MAX_LOGIN_ATTEMPTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('leetcode_login.log')
    ]
)

# State file path
STATE_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leetcode_state.json')


def parse_credentials_from_env():
    """
    Parse credentials from environment variable LEET_CREDS.
    
    Expected format: user1:pass1,user2:pass2,user3:pass3
    
    Returns:
        list: List of credential dictionaries with 'username' and 'password' keys
    """
    try:
        leet_creds = os.getenv('LEET_CREDS', '').strip()
        
        if not leet_creds:
            logging.info("No LEET_CREDS environment variable found")
            return []
        
        accounts = []
        credential_pairs = leet_creds.split(',')
        
        for i, pair in enumerate(credential_pairs):
            pair = pair.strip()
            if not pair:
                continue
                
            if ':' not in pair:
                logging.warning(f"Invalid credential format at position {i+1}: '{pair}' (expected 'username:password')")
                continue
            
            # Split only on the first colon to handle passwords with colons
            username, password = pair.split(':', 1)
            username = username.strip()
            password = password.strip()
            
            if not username or not password:
                logging.warning(f"Empty username or password at position {i+1}: '{pair}'")
                continue
            
            accounts.append({
                "username": username,
                "password": password
            })
            # Log without exposing password
            logging.info(f"Loaded account {i+1}: {username} (password: {'*' * min(len(password), 8)})")
        
        if accounts:
            logging.info(f"Successfully loaded {len(accounts)} accounts from environment variables")
        else:
            logging.warning("No valid accounts found in LEET_CREDS environment variable")
        
        return accounts
        
    except Exception as e:
        logging.error(f"Error parsing credentials from environment: {str(e)}")
        return []


def check_credential_setup():
    """
    Check and provide feedback on credential setup.
    
    Returns:
        dict: Status information about credential setup
    """
    status = {
        'has_env_var': bool(os.getenv('LEET_CREDS')),
        'has_env_file': False,
        'env_accounts_count': 0,
        'env_accounts_valid': False
    }
    
    # Check for .env file
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file_path):
        status['has_env_file'] = True
        with open(env_file_path, 'r') as f:
            env_content = f.read()
            if 'LEET_CREDS=' in env_content:
                status['has_env_var'] = True
    
    # Check validity of environment accounts
    if status['has_env_var']:
        env_accounts = parse_credentials_from_env()
        status['env_accounts_count'] = len(env_accounts)
        status['env_accounts_valid'] = len(env_accounts) > 0
    
    return status


def get_accounts_from_config():
    """
    Get accounts from environment variables, falling back to hardcoded config if needed.
    
    Returns:
        list: List of account dictionaries
    """
    # Check credential setup status
    cred_status = check_credential_setup()
    
    # Try to get accounts from environment variables first
    env_accounts = parse_credentials_from_env()
    
    if env_accounts:
        source = "environment variable" if not cred_status['has_env_file'] else ".env file"
        print(f"✅ Loaded {len(env_accounts)} accounts from {source}")
        return env_accounts
    
    # Fallback to hardcoded accounts (now empty by default)
    hardcoded_accounts = [
        # Add your accounts here if not using environment variables:
        # {"username": "your_username", "password": "your_password"},
    ]
    
    if hardcoded_accounts:
        print(f"⚠️  Using {len(hardcoded_accounts)} hardcoded accounts (consider using LEET_CREDS environment variable)")
        logging.warning("Using hardcoded accounts - consider using environment variables for security")
        return hardcoded_accounts
    
    # No accounts found - provide helpful setup instructions
    print("🔧 No accounts configured. Here's how to set them up:")
    print()
    if not cred_status['has_env_var']:
        print("📝 OPTION 1: Environment Variable")
        print("   export LEET_CREDS='user1@example.com:pass1,user2@example.com:pass2'")
        print()
        print("📝 OPTION 2: Create .env file")
        print("   echo 'LEET_CREDS=user1@example.com:pass1,user2@example.com:pass2' > .env")
        print()
        print("📝 OPTION 3: Interactive setup (will prompt when running)")
        print()
    else:
        if cred_status['env_accounts_count'] == 0:
            print("❌ LEET_CREDS environment variable found but no valid accounts parsed")
            print("   Check format: 'user1:pass1,user2:pass2'")
            print("   Current value:", os.getenv('LEET_CREDS', '')[:50] + "..." if len(os.getenv('LEET_CREDS', '')) > 50 else os.getenv('LEET_CREDS', ''))
    
    return []


# Multi-account configuration
MULTI_ACCOUNT_CONFIG = {
    "enabled": True,  # Set to True to enable multi-account mode
    "max_workers": 1,  # Number of parallel browser instances
    "accounts": get_accounts_from_config()  # Load accounts from environment variables
}


class MultiAccountManager:
    """Manages multiple LeetCode accounts with separate browser instances."""
    
    def __init__(self, accounts, max_workers=3):
        self.accounts = accounts
        self.max_workers = min(max_workers, len(accounts))
        self.drivers = {}
        self.account_cookies = {}
        self.account_headers = {}
        self.work_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.lock = threading.Lock()
        
    def initialize_drivers(self):
        """Initialize undetected WebDriver instances for each account."""
        logging.info(f"Initializing {self.max_workers} undetected browser instances...")
        print(f"\n🚀 Starting {self.max_workers} undetected Chrome browsers...")
        print("📱 Each browser will appear as a separate window")
        print("🔍 Using undetected-chromedriver to bypass bot detection")
        print("⚡ This should significantly reduce Cloudflare challenges")
        
        for i in range(self.max_workers):
            account = self.accounts[i % len(self.accounts)]
            account_id = f"account_{i}"
            
            try:
                print(f"🔧 Initializing browser {i+1}/{self.max_workers} for {account['username']}...")
                
                # Initialize driver with unique settings
                driver = self._create_driver_with_unique_fingerprint(i)
                self.drivers[account_id] = {
                    "driver": driver,
                    "account": account,
                    "is_logged_in": False,
                    "last_used": time.time()
                }
                logging.info(f"✅ Initialized undetected driver for {account_id}")
                print(f"✅ Browser {i+1} ready: {account['username']}")
            except Exception as e:
                logging.error(f"❌ Failed to initialize driver for {account_id}: {str(e)}")
                print(f"❌ Failed to initialize browser {i+1}: {str(e)}")
        
        success_count = len(self.drivers)
        if success_count > 0:
            print(f"\n🎉 Successfully initialized {success_count}/{self.max_workers} browsers")
            print("💡 Look for browser windows titled 'LeetCode Bot - Account X'")
            print("🔄 Starting login process...")
        
        return success_count > 0
    
    def _create_driver_with_unique_fingerprint(self, instance_id):
        """Create an undetected WebDriver with unique fingerprint to avoid detection."""
        import undetected_chromedriver as uc
        
        # Create undetected Chrome options
        options = uc.ChromeOptions()
        
        # Add essential options (avoid headless mode for better detection avoidance)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Speed up loading
        
        # Unique window size for each instance
        window_sizes = [(1920, 1080), (1366, 768), (1440, 900)]
        window_size = window_sizes[instance_id % len(window_sizes)]
        options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        # Unique profile directory for each instance
        profile_dir = f"./chrome_profiles/profile_{instance_id}"
        options.add_argument(f'--user-data-dir={profile_dir}')
        
        # Grid positioning for easy window management
        window_positions = [(0, 0), (640, 0), (1280, 0)]  # 3-column layout
        window_position = window_positions[instance_id % len(window_positions)]
        options.add_argument(f'--window-position={window_position[0]},{window_position[1]}')
        
        # Create undetected Chrome driver
        driver = uc.Chrome(options=options, version_main=None)
        
        # Set browser title for identification
        driver.execute_script(f"document.title = 'LeetCode Bot - Account {instance_id + 1}';")
        
        # Set timeouts
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(IMPLICIT_WAIT)
        
        return driver
    
    def login_all_accounts(self):
        """Login to all accounts serially (one by one) for better reliability."""
        logging.info("Starting serial login process...")
        
        logged_in_count = 0
        
        for account_id, account_data in self.drivers.items():
            try:
                result = self._login_account(account_id, account_data)
                if result:
                    logged_in_count += 1
                    logging.info(f"✅ Login successful for {result} ({logged_in_count}/{len(self.drivers)})")
                else:
                    logging.error(f"❌ Login failed for {account_id}")
                    
                # Small delay between logins to avoid overwhelming the server
                if account_id != list(self.drivers.keys())[-1]:  # Not the last account
                    time.sleep(2)
                    
            except Exception as e:
                logging.error(f"❌ Login exception for {account_id}: {str(e)}")
        
        logging.info(f"Successfully logged in to {logged_in_count}/{len(self.drivers)} accounts")
        return logged_in_count > 0
    
    def _login_account(self, account_id, account_data):
        """Login to a specific account."""
        driver = account_data["driver"]
        account = account_data["account"]
        
        try:
            logging.info(f"Logging in {account_id} ({account['username']})")
            
            # Navigate to login page
            driver.get(LOGIN_URL)
            wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
            
            # Perform login
            perform_login(driver, wait, account["username"], account["password"])
            
            # Verify login
            if verify_login_status(driver, wait):
                # Get and store cookies/headers
                cookies_dict, headers = get_cookies_and_headers(driver)
                
                with self.lock:
                    self.account_cookies[account_id] = cookies_dict
                    self.account_headers[account_id] = headers
                    account_data["is_logged_in"] = True
                
                logging.info(f"✅ {account_id} logged in successfully")
                return account_id
            else:
                logging.error(f"❌ {account_id} login verification failed")
                return None
                
        except Exception as e:
            logging.error(f"❌ {account_id} login error: {str(e)}")
            return None
    
    def get_available_account(self):
        """Get an available account for making requests."""
        with self.lock:
            # Find account that was used least recently
            available_accounts = [
                (account_id, data) for account_id, data in self.drivers.items() 
                if data["is_logged_in"]
            ]
            
            if not available_accounts:
                return None, None, None
            
            # Sort by last used time (oldest first)
            available_accounts.sort(key=lambda x: x[1]["last_used"])
            account_id, account_data = available_accounts[0]
            
            # Update last used time
            account_data["last_used"] = time.time()
            
            return (
                account_id,
                self.account_cookies.get(account_id),
                self.account_headers.get(account_id)
            )
    
    def divide_workload(self, problem_files, start_index=0):
        """Divide workload evenly among available workers.
        
        Args:
            problem_files: List of problem files
            start_index: Starting index for processing
            
        Returns:
            List of tuples (worker_id, start_idx, end_idx, assigned_problems)
        """
        # Get available accounts
        available_accounts = [
            account_id for account_id, data in self.drivers.items() 
            if data["is_logged_in"]
        ]
        
        if not available_accounts:
            return []
        
        # Calculate workload division
        total_problems = len(problem_files) - start_index
        problems_per_worker = total_problems // len(available_accounts)
        remaining_problems = total_problems % len(available_accounts)
        
        workload_assignments = []
        current_index = start_index
        
        for i, account_id in enumerate(available_accounts):
            # Calculate range for this worker
            worker_start = current_index
            worker_problems = problems_per_worker
            
            # Distribute remaining problems to first few workers
            if i < remaining_problems:
                worker_problems += 1
            
            worker_end = worker_start + worker_problems
            
            # Get assigned problem files
            assigned_problems = problem_files[worker_start:worker_end]
            
            workload_assignments.append((
                account_id,
                worker_start,
                worker_end,
                assigned_problems
            ))
            
            current_index = worker_end
            
            # Log assignment
            logging.info(f"📋 {account_id}: Problems {worker_start + 1}-{worker_end} ({len(assigned_problems)} problems)")
        
        return workload_assignments
    
    def process_problems_parallel(self, problem_files, start_index=0):
        """Process problems in parallel with divided workload among workers."""
        # Check for existing worker states
        worker_states = self.check_worker_states()
        
        if worker_states:
            print(f"\n{'='*80}")
            print("WORKER STATES DETECTED")
            print(f"{'='*80}")
            print(f"Found existing state files for {len(worker_states)} workers:")
            
            for worker_id, state_info in worker_states.items():
                print(f"🤖 {worker_id}: Last processed problem {state_info['last_processed_index'] + 1} ({state_info['last_processed_problem']})")
                print(f"   Next problem: {state_info['next_problem_index'] + 1}, Timestamp: {state_info['timestamp']}")
            
            print(f"{'='*80}")
            
            # Ask user about resumption
            print("\nWhat would you like to do?")
            print("1. Resume from where each worker left off")
            print("2. Start fresh (clear all worker states)")
            print("3. Cancel and exit")
            
            choice = input("Enter your choice (1/2/3): ").strip()
            
            if choice == "1":
                print("✅ Resuming from existing worker states...")
                # Don't modify workload division - each worker will check its own state
            elif choice == "2":
                print("🔄 Clearing all worker states...")
                self.clear_all_worker_states()
                print("✅ All worker states cleared")
            elif choice == "3":
                print("❌ Operation cancelled")
                return False
            else:
                print("❌ Invalid choice, cancelling...")
                return False
        
        # Divide workload among available workers
        workload_assignments = self.divide_workload(problem_files, start_index)
        
        if not workload_assignments:
            logging.error("No available workers for processing")
            return
        
        print(f"\n{'='*80}")
        print("WORKLOAD DIVISION")
        print(f"{'='*80}")
        print(f"Total problems to process: {len(problem_files) - start_index}")
        print(f"Available workers: {len(workload_assignments)}")
        print(f"{'='*80}")
        
        for account_id, start_idx, end_idx, assigned_problems in workload_assignments:
            print(f"🤖 {account_id}: Problems {start_idx + 1}-{end_idx} ({len(assigned_problems)} problems)")
        
        print(f"{'='*80}")
        
        # Show workload distribution info
        problem_counts = [len(assigned_problems) for _, _, _, assigned_problems in workload_assignments]
        min_problems = min(problem_counts)
        max_problems = max(problem_counts)
        avg_problems = sum(problem_counts) / len(problem_counts)
        
        print(f"📊 Workload Distribution:")
        print(f"   • Min problems per worker: {min_problems}")
        print(f"   • Max problems per worker: {max_problems}")
        print(f"   • Average problems per worker: {avg_problems:.1f}")
        print(f"   • Load balance variance: {max_problems - min_problems}")
        print(f"{'='*80}")
        
        # Estimate completion time
        estimated_time_per_problem = 10  # seconds (rough estimate)
        estimated_total_time = max_problems * estimated_time_per_problem
        estimated_minutes = estimated_total_time / 60
        
        print(f"⏱️  Estimated completion time: ~{estimated_minutes:.1f} minutes")
        print(f"   (Based on {estimated_time_per_problem}s per problem, slowest worker determines total time)")
        print(f"{'='*80}")
        
        # Additional info about state files
        print(f"\n🗂️  State Management:")
        print(f"   • Each worker maintains its own state file")
        print(f"   • State files: leetcode_state_account_0.json, leetcode_state_account_1.json, etc.")
        print(f"   • Workers can resume independently if interrupted")
        print(f"   • Enhanced retry logic: 5 exponential backoff attempts")
        
        # Confirm before starting
        print(f"\n💡 Workers will process their assigned problems independently.")
        print(f"   Each worker uses a separate account to bypass individual rate limits.")
        print(f"   Progress will be tracked per worker and overall.")
        
        start_confirmation = input(f"\nReady to start parallel processing? (y/n): ").strip().lower()
        if start_confirmation not in ['y', 'yes']:
            print("❌ Processing cancelled by user")
            return False
        
        print(f"\n🚀 Starting parallel processing...")
        print(f"{'='*80}")
        
        # Process problems with thread pool
        with ThreadPoolExecutor(max_workers=len(workload_assignments)) as executor:
            futures = []
            
            for assignment in workload_assignments:
                future = executor.submit(self._worker_process_assigned_problems, assignment)
                futures.append(future)
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Worker error: {str(e)}")
        
        print(f"\n✅ All workers completed their assigned workloads")
        return True
    
    def _worker_process_assigned_problems(self, assignment):
        """Worker function to process assigned problems range.
        
        Args:
            assignment: Tuple of (account_id, start_idx, end_idx, assigned_problems)
        """
        account_id, start_idx, end_idx, assigned_problems = assignment
        
        try:
            logging.info(f"🚀 [{account_id}] Starting assigned workload: {len(assigned_problems)} problems")
            
            # Check for existing worker state
            worker_state = load_state(worker_id=account_id)
            resume_from_index = 0
            
            if worker_state:
                last_processed_index = worker_state.get("last_processed_index", -1)
                # Find where to resume within this worker's assigned problems
                for i, problem_file in enumerate(assigned_problems):
                    problem_index = start_idx + i
                    if problem_index > last_processed_index:
                        resume_from_index = i
                        break
                else:
                    # All problems in this worker's assignment were already processed
                    logging.info(f"✅ [{account_id}] All assigned problems already processed")
                    return
                
                if resume_from_index > 0:
                    logging.info(f"🔄 [{account_id}] Resuming from problem {resume_from_index + 1}/{len(assigned_problems)}")
                    print(f"🔄 [{account_id}] Resuming from problem {resume_from_index + 1}/{len(assigned_problems)}")
            
            # Process problems starting from resume_from_index
            for i in range(resume_from_index, len(assigned_problems)):
                problem_file = assigned_problems[i]
                problem_index = start_idx + i
                problem_name = problem_file[:-3]  # Remove .py extension
                python_file_path = os.path.join("Leet_complete", problem_name, problem_file)
                
                logging.info(f"🔄 [{account_id}] Processing {problem_name} ({i + 1}/{len(assigned_problems)})")
                
                # Check if problem is already completed
                if is_problem_already_completed(problem_name):
                    logging.info(f"✅ [{account_id}] Problem {problem_name} already completed successfully - skipping")
                    print(f"✅ [{account_id}] {problem_name} - ALREADY COMPLETED")
                    result = "success"
                else:
                    # Get account credentials
                    with self.lock:
                        cookies = self.account_cookies.get(account_id)
                        headers = self.account_headers.get(account_id)
                        driver = self.drivers[account_id]["driver"]
                    
                    if not cookies or not headers:
                        logging.error(f"❌ [{account_id}] Missing credentials for {problem_name}")
                        continue
                    
                    # Submit using the account's credentials
                    result = self._submit_with_account(account_id, problem_name, python_file_path, cookies, headers)
                
                # Store result
                self.results_queue.put((problem_index, problem_name, result, account_id))
                
                # Save state after each problem (worker-specific)
                status = "success" if result == "success" else "failed"
                save_state(problem_index, problem_name, status, len(assigned_problems), 0, 0, 0, worker_id=account_id)
                
                # Progress update
                progress = ((i + 1) / len(assigned_problems)) * 100
                logging.info(f"📊 [{account_id}] Progress: {progress:.1f}% ({i + 1}/{len(assigned_problems)})")
                
                # Small delay between submissions
                time.sleep(0.5)
                
        except Exception as e:
            logging.error(f"❌ [{account_id}] Worker error: {str(e)}")
        
        logging.info(f"✅ [{account_id}] Completed assigned workload")
    
    def _worker_process_problems(self):
        """Worker function to process problems from the queue."""
        while True:
            try:
                # Get next problem from queue (with timeout)
                problem_index, problem_file = self.work_queue.get(timeout=5)
                
                # Get available account
                account_id, cookies, headers = self.get_available_account()
                if not account_id:
                    logging.error("No available accounts for processing")
                    self.work_queue.task_done()
                    continue
                
                # Process the problem
                problem_name = problem_file[:-3]  # Remove .py extension
                python_file_path = os.path.join("Leet_complete", problem_name, problem_file)
                
                logging.info(f"🔄 [{account_id}] Processing {problem_name}")
                
                # Submit using the account's cookies and headers
                result = self._submit_with_account(account_id, problem_name, python_file_path, cookies, headers)
                
                # Store result
                self.results_queue.put((problem_index, problem_name, result, account_id))
                
                # Mark task as done
                self.work_queue.task_done()
                
                # Small delay to avoid overwhelming
                time.sleep(0.5)
                
            except queue.Empty:
                # No more items in queue
                break
            except Exception as e:
                logging.error(f"Worker error processing problem: {str(e)}")
                self.work_queue.task_done()
    
    def _submit_with_account(self, account_id, problem_name, python_file_path, cookies, headers):
        """Submit a problem using specific account credentials."""
        try:
            # Use the existing submit function but with specific cookies/headers
            # We'll need to modify submit_code_to_leetcode to accept cookies/headers
            
            # For now, get the driver for this account for backup
            driver = self.drivers[account_id]["driver"]
            
            # Submit the code (this will use the driver's current session)
            submission_id = submit_code_to_leetcode(driver, problem_name, python_file_path)
            
            if submission_id and submission_id not in ["403_ERROR", "PREMIUM_REQUIRED", "LOGIN_REQUIRED"]:
                # Wait for result
                result = wait_for_submission_result(driver, submission_id)
                if result:
                    state = result.get('state', 'UNKNOWN')
                    if state == 'SUCCESS':
                        # Document the success
                        document_problem(driver, problem_name, result, submission_id)
                        return "success"
                    else:
                        return "failed"
                else:
                    return "failed"
            else:
                return submission_id if submission_id else "failed"
                
        except Exception as e:
            logging.error(f"[{account_id}] Submission error: {str(e)}")
            return "failed"
    
    def check_worker_states(self):
        """Check for existing worker state files and return resumption info.
        
        Returns:
            dict: Dictionary mapping worker IDs to their state information
        """
        worker_states = {}
        
        for account_id in self.drivers.keys():
            state = load_state(worker_id=account_id)
            if state:
                worker_states[account_id] = {
                    "last_processed_index": state.get("last_processed_index", 0),
                    "last_processed_problem": state.get("last_processed_problem", "Unknown"),
                    "next_problem_index": state.get("next_problem_index", 0),
                    "timestamp": state.get("timestamp", "Unknown")
                }
        
        return worker_states
    
    def cleanup(self):
        """Clean up all WebDriver instances."""
        logging.info("Cleaning up browser instances...")
        for account_id, account_data in self.drivers.items():
            try:
                account_data["driver"].quit()
                logging.info(f"✅ Cleaned up {account_id}")
            except Exception as e:
                logging.error(f"❌ Error cleaning up {account_id}: {str(e)}")
        
        # Clean up profile directories
        import shutil
        try:
            if os.path.exists("./chrome_profiles"):
                shutil.rmtree("./chrome_profiles")
        except Exception as e:
            logging.warning(f"Could not clean up profile directories: {str(e)}")
    
    def clear_all_worker_states(self):
        """Clear all worker state files."""
        for account_id in self.drivers.keys():
            clear_state(worker_id=account_id)
    
    def show_worker_progress(self):
        """Show current progress of all workers."""
        print(f"\n{'='*80}")
        print("WORKER PROGRESS STATUS")
        print(f"{'='*80}")
        
        worker_states = self.check_worker_states()
        
        if not worker_states:
            print("No worker state files found.")
            return
        
        for worker_id, state_info in worker_states.items():
            print(f"🤖 {worker_id}:")
            print(f"   • Last processed: Problem {state_info['last_processed_index'] + 1} ({state_info['last_processed_problem']})")
            print(f"   • Next to process: Problem {state_info['next_problem_index'] + 1}")
            print(f"   • Last update: {state_info['timestamp']}")
            print()
        
        print(f"{'='*80}")
    
    def parse_failed_problems_from_results(self, results_file_path):
        """Parse a results JSON file and extract failed problems.
        
        Args:
            results_file_path: Path to the results JSON file
            
        Returns:
            list: List of failed problem dictionaries
        """
        try:
            with open(results_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract failed problems
            failed_problems = []
            for result in data.get('results', []):
                if result.get('result') == 'failed':
                    failed_problems.append({
                        'problem_index': result.get('problem_index'),
                        'problem_name': result.get('problem_name'),
                        'original_account_id': result.get('account_id')
                    })
            
            logging.info(f"Found {len(failed_problems)} failed problems in {results_file_path}")
            return failed_problems
            
        except Exception as e:
            logging.error(f"Error parsing results file {results_file_path}: {str(e)}")
            return []
    
    def parse_problems_from_todo_file(self, todo_file_path):
        """Parse a todo JSON file and extract problem names.
        
        Args:
            todo_file_path: Path to the todo JSON file
            
        Returns:
            list: List of problem names
        """
        try:
            with open(todo_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract problems from the JSON
            problems = data.get('problems', [])
            
            if not problems:
                logging.warning(f"No problems found in {todo_file_path}")
                return []
            
            # Validate that each problem has a corresponding Python file
            leet_complete_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Leet_complete")
            valid_problems = []
            missing_problems = []
            
            for problem_name in problems:
                python_file_path = os.path.join(leet_complete_folder, problem_name, f"{problem_name}.py")
                if os.path.exists(python_file_path):
                    valid_problems.append(problem_name)
                else:
                    missing_problems.append(problem_name)
            
            if missing_problems:
                logging.warning(f"Missing Python files for {len(missing_problems)} problems: {missing_problems[:5]}...")
                print(f"⚠️  Warning: {len(missing_problems)} problems don't have corresponding Python files")
                if len(missing_problems) <= 10:
                    print(f"   Missing files: {missing_problems}")
                else:
                    print(f"   First 10 missing files: {missing_problems[:10]}")
            
            logging.info(f"Found {len(valid_problems)} valid problems from {todo_file_path}")
            return valid_problems
            
        except Exception as e:
            logging.error(f"Error parsing todo file {todo_file_path}: {str(e)}")
            return []
    
    def divide_failed_problems_among_workers(self, failed_problems):
        """Divide failed problems evenly among available workers.
        
        Args:
            failed_problems: List of failed problem dictionaries
            
        Returns:
            dict: Dictionary mapping worker IDs to their assigned failed problems
        """
        available_workers = [
            account_id for account_id, data in self.drivers.items() 
            if data["is_logged_in"]
        ]
        
        if not available_workers:
            return {}
        
        # Divide problems evenly
        problems_per_worker = len(failed_problems) // len(available_workers)
        remaining_problems = len(failed_problems) % len(available_workers)
        
        worker_assignments = {}
        current_index = 0
        
        for i, worker_id in enumerate(available_workers):
            # Calculate how many problems this worker gets
            worker_problems = problems_per_worker
            if i < remaining_problems:
                worker_problems += 1
            
            # Assign problems to this worker
            worker_assignments[worker_id] = failed_problems[current_index:current_index + worker_problems]
            current_index += worker_problems
        
        return worker_assignments
    
    def process_failed_problems_from_results(self, results_file_path):
        """Process failed problems from a results JSON file.
        
        Args:
            results_file_path: Path to the results JSON file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Parse failed problems from results file
            failed_problems = self.parse_failed_problems_from_results(results_file_path)
            
            if not failed_problems:
                print("❌ No failed problems found in the results file")
                return False
            
            print(f"\n{'='*80}")
            print("FAILED PROBLEMS RETRY PROCESSING")
            print(f"{'='*80}")
            print(f"Results file: {results_file_path}")
            print(f"Failed problems found: {len(failed_problems)}")
            print(f"Available workers: {len([w for w in self.drivers.values() if w['is_logged_in']])}")
            print(f"{'='*80}")
            
            # Divide failed problems among workers
            worker_assignments = self.divide_failed_problems_among_workers(failed_problems)
            
            if not worker_assignments:
                print("❌ No available workers for processing")
                return False
            
            # Show assignment distribution
            print("\n📋 FAILED PROBLEMS ASSIGNMENT:")
            for worker_id, assigned_problems in worker_assignments.items():
                print(f"🤖 {worker_id}: {len(assigned_problems)} failed problems")
                if assigned_problems:
                    print(f"   • First: {assigned_problems[0]['problem_name']}")
                    print(f"   • Last: {assigned_problems[-1]['problem_name']}")
            
            print(f"\n{'='*80}")
            
            # Ask for confirmation
            print("🔄 This will retry only the failed problems from the results file.")
            print("💡 Each worker will process its assigned failed problems independently.")
            print("🗂️  Worker-specific state files will track retry progress.")
            
            confirm = input("\nProceed with failed problems retry? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Failed problems retry cancelled by user")
                return False
            
            print(f"\n🚀 Starting failed problems retry processing...")
            print(f"{'='*80}")
            
            # Process failed problems with thread pool
            with ThreadPoolExecutor(max_workers=len(worker_assignments)) as executor:
                futures = []
                
                for worker_id, assigned_problems in worker_assignments.items():
                    future = executor.submit(self._worker_process_failed_problems, worker_id, assigned_problems)
                    futures.append(future)
                
                # Wait for all workers to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Worker error during failed problems retry: {str(e)}")
            
            print(f"\n✅ All workers completed failed problems retry")
            return True
            
        except Exception as e:
            logging.error(f"Error processing failed problems from results: {str(e)}")
            print(f"❌ Error processing failed problems: {str(e)}")
            return False
    
    def process_problems_from_todo_file(self, todo_file_path):
        """Process problems from a todo JSON file.
        
        Args:
            todo_file_path: Path to the todo JSON file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Parse problems from todo file
            problem_names = self.parse_problems_from_todo_file(todo_file_path)
            
            if not problem_names:
                print("❌ No valid problems found in the todo file")
                return False
            
            print(f"\n{'='*80}")
            print("TODO FILE PROCESSING")
            print(f"{'='*80}")
            print(f"Todo file: {todo_file_path}")
            print(f"Problems found: {len(problem_names)}")
            print(f"Available workers: {len([w for w in self.drivers.values() if w['is_logged_in']])}")
            print(f"{'='*80}")
            
            # Convert problem names to the format expected by the existing processing logic
            # Create mock problem files list that matches the expected format
            problem_files = [f"{problem_name}.py" for problem_name in problem_names]
            
            # Show some example problems
            print("\n📝 PROBLEMS TO PROCESS:")
            for i, problem_name in enumerate(problem_names[:10]):  # Show first 10
                print(f"   {i+1}. {problem_name}")
            
            if len(problem_names) > 10:
                print(f"   ... and {len(problem_names) - 10} more problems")
            
            # Divide problems among workers
            worker_assignments = self.divide_workload(problem_files, 0)
            
            if not worker_assignments:
                print("❌ No available workers for processing")
                return False
            
            # Show assignment distribution
            print("\n📋 TODO PROBLEMS ASSIGNMENT:")
            for account_id, start_idx, end_idx, assigned_problems in worker_assignments:
                print(f"🤖 {account_id}: {len(assigned_problems)} problems")
                if assigned_problems:
                    # Extract problem names from filenames
                    first_problem = assigned_problems[0][:-3]  # Remove .py extension
                    last_problem = assigned_problems[-1][:-3]  # Remove .py extension
                    print(f"   • First: {first_problem}")
                    print(f"   • Last: {last_problem}")
            
            print(f"\n{'='*80}")
            
            # Ask for confirmation
            print("🔄 This will process problems from the todo file.")
            print("💡 Each worker will process its assigned problems independently.")
            print("🗂️  Worker-specific state files will track processing progress.")
            
            confirm = input("\nProceed with todo file processing? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("❌ Todo file processing cancelled by user")
                return False
            
            print(f"\n🚀 Starting todo file processing...")
            print(f"{'='*80}")
            
            # Process problems with thread pool using specialized todo processing
            with ThreadPoolExecutor(max_workers=len(worker_assignments)) as executor:
                futures = []
                
                for assignment in worker_assignments:
                    future = executor.submit(self._worker_process_todo_problems, assignment)
                    futures.append(future)
                
                # Wait for all workers to complete
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Worker error during todo file processing: {str(e)}")
            
            print(f"\n✅ All workers completed todo file processing")
            return True
            
        except Exception as e:
            logging.error(f"Error processing todo file: {str(e)}")
            print(f"❌ Error processing todo file: {str(e)}")
            return False
    
    def _worker_process_failed_problems(self, worker_id, assigned_problems):
        """Worker function to process assigned failed problems.
        
        Args:
            worker_id: ID of the worker account
            assigned_problems: List of failed problem dictionaries assigned to this worker
        """
        try:
            logging.info(f"🚀 [{worker_id}] Starting failed problems retry: {len(assigned_problems)} problems")
            print(f"🚀 [{worker_id}] Starting failed problems retry: {len(assigned_problems)} problems")
            
            for i, problem_info in enumerate(assigned_problems):
                problem_name = problem_info['problem_name']
                problem_index = problem_info['problem_index']
                python_file_path = os.path.join("Leet_complete", problem_name, f"{problem_name}.py")
                
                logging.info(f"🔄 [{worker_id}] Retrying {problem_name} ({i + 1}/{len(assigned_problems)})")
                print(f"🔄 [{worker_id}] Retrying {problem_name} ({i + 1}/{len(assigned_problems)})")
                
                # Check if problem is already completed
                if is_problem_already_completed(problem_name):
                    logging.info(f"✅ [{worker_id}] Problem {problem_name} already completed successfully - skipping retry")
                    print(f"✅ [{worker_id}] {problem_name} - ALREADY COMPLETED")
                    result = "success"
                else:
                    # Check if Python file exists
                    if not os.path.exists(python_file_path):
                        logging.warning(f"⚠️  [{worker_id}] Python file not found: {python_file_path}")
                        continue
                    
                    # Get account credentials
                    with self.lock:
                        cookies = self.account_cookies.get(worker_id)
                        headers = self.account_headers.get(worker_id)
                        driver = self.drivers[worker_id]["driver"]
                    
                    if not cookies or not headers:
                        logging.error(f"❌ [{worker_id}] Missing credentials for {problem_name}")
                        continue
                    
                    # Submit using the account's credentials
                    result = self._submit_with_account(worker_id, problem_name, python_file_path, cookies, headers)
                
                # Store result
                self.results_queue.put((problem_index, problem_name, result, worker_id))
                
                # Save state for retry tracking
                status = "success" if result == "success" else "failed"
                save_state(problem_index, problem_name, status, len(assigned_problems), 0, 0, 0, worker_id=f"{worker_id}_retry")
                
                # Progress update
                progress = ((i + 1) / len(assigned_problems)) * 100
                logging.info(f"📊 [{worker_id}] Retry progress: {progress:.1f}% ({i + 1}/{len(assigned_problems)})")
                
                # Result logging
                if result == "success":
                    print(f"✅ [{worker_id}] {problem_name} - SUCCESS on retry")
                elif result == "PREMIUM_REQUIRED":
                    print(f"🔒 [{worker_id}] {problem_name} - PREMIUM REQUIRED")
                elif result == "LOGIN_REQUIRED":
                    print(f"🔑 [{worker_id}] {problem_name} - LOGIN REQUIRED")
                else:
                    print(f"❌ [{worker_id}] {problem_name} - FAILED again")
                
                # Small delay between submissions
                time.sleep(0.5)
                
        except Exception as e:
            logging.error(f"❌ [{worker_id}] Worker error during failed problems retry: {str(e)}")
        
        logging.info(f"✅ [{worker_id}] Completed failed problems retry")
        print(f"✅ [{worker_id}] Completed failed problems retry")
    
    def _worker_process_todo_problems(self, assignment):
        """Worker function to process assigned todo problems with separate state management.
        
        Args:
            assignment: Tuple of (account_id, start_idx, end_idx, assigned_problems)
        """
        account_id, start_idx, end_idx, assigned_problems = assignment
        
        try:
            logging.info(f"🚀 [{account_id}] Starting todo workload: {len(assigned_problems)} problems")
            print(f"🚀 [{account_id}] Starting todo workload: {len(assigned_problems)} problems")
            
            # Use separate state files for todo processing
            worker_state = load_state(worker_id=f"{account_id}_todo")
            resume_from_index = 0
            
            if worker_state:
                last_processed_problem = worker_state.get("last_processed_problem", "")
                
                # Find where to resume within this worker's assigned problems
                for i, problem_file in enumerate(assigned_problems):
                    problem_name = problem_file[:-3]  # Remove .py extension
                    if problem_name == last_processed_problem:
                        resume_from_index = i + 1  # Resume from next problem
                        break
                
                if resume_from_index > 0:
                    logging.info(f"🔄 [{account_id}] Resuming from problem {resume_from_index + 1}/{len(assigned_problems)}")
                    print(f"🔄 [{account_id}] Resuming from problem {resume_from_index + 1}/{len(assigned_problems)}")
                elif resume_from_index == 0 and last_processed_problem:
                    # Check if we've already processed all problems
                    last_problem_in_assignment = assigned_problems[-1][:-3]
                    if last_processed_problem == last_problem_in_assignment:
                        logging.info(f"✅ [{account_id}] All todo problems already processed")
                        print(f"✅ [{account_id}] All todo problems already processed")
                        return
            
            # Process problems starting from resume_from_index
            for i in range(resume_from_index, len(assigned_problems)):
                problem_file = assigned_problems[i]
                problem_name = problem_file[:-3]  # Remove .py extension
                python_file_path = os.path.join("Leet_complete", problem_name, problem_file)
                
                logging.info(f"🔄 [{account_id}] Processing {problem_name} ({i + 1}/{len(assigned_problems)})")
                print(f"🔄 [{account_id}] Processing {problem_name} ({i + 1}/{len(assigned_problems)})")
                
                # Check if problem is already completed
                if is_problem_already_completed(problem_name):
                    logging.info(f"✅ [{account_id}] Problem {problem_name} already completed successfully - skipping")
                    print(f"✅ [{account_id}] {problem_name} - ALREADY COMPLETED")
                    result = "success"
                else:
                    # Check if Python file exists
                    if not os.path.exists(python_file_path):
                        logging.warning(f"⚠️  [{account_id}] Python file not found: {python_file_path}")
                        continue
                    
                    # Get account credentials
                    with self.lock:
                        cookies = self.account_cookies.get(account_id)
                        headers = self.account_headers.get(account_id)
                        driver = self.drivers[account_id]["driver"]
                    
                    if not cookies or not headers:
                        logging.error(f"❌ [{account_id}] Missing credentials for {problem_name}")
                        continue
                    
                    # Submit using the account's credentials
                    result = self._submit_with_account(account_id, problem_name, python_file_path, cookies, headers)
                
                # Store result (use todo-specific index)
                todo_index = start_idx + i
                self.results_queue.put((todo_index, problem_name, result, account_id))
                
                # Save state after each problem (using todo-specific worker ID)
                status = "success" if result == "success" else "failed"
                save_state(todo_index, problem_name, status, len(assigned_problems), 0, 0, 0, worker_id=f"{account_id}_todo")
                
                # Progress update
                progress = ((i + 1) / len(assigned_problems)) * 100
                logging.info(f"📊 [{account_id}] Todo progress: {progress:.1f}% ({i + 1}/{len(assigned_problems)})")
                
                # Result logging
                if result == "success":
                    print(f"✅ [{account_id}] {problem_name} - SUCCESS")
                elif result == "PREMIUM_REQUIRED":
                    print(f"🔒 [{account_id}] {problem_name} - PREMIUM REQUIRED")
                elif result == "LOGIN_REQUIRED":
                    print(f"🔑 [{account_id}] {problem_name} - LOGIN REQUIRED")
                else:
                    print(f"❌ [{account_id}] {problem_name} - FAILED")
                
                # Small delay between submissions
                time.sleep(0.5)
                
        except Exception as e:
            logging.error(f"❌ [{account_id}] Worker error during todo processing: {str(e)}")
        
        logging.info(f"✅ [{account_id}] Completed todo workload")
        print(f"✅ [{account_id}] Completed todo workload")


def get_multi_account_credentials():
    """Get credentials for multiple accounts interactively."""
    accounts = []
    
    print("\n" + "="*60)
    print("INTERACTIVE MULTI-ACCOUNT SETUP")
    print("="*60)
    print("💡 TIP: For automated setup, use environment variables:")
    print("   export LEET_CREDS='user1:pass1,user2:pass2'")
    print("   or create a .env file with: LEET_CREDS=user1:pass1,user2:pass2")
    print("="*60)
    print("Enter credentials for multiple LeetCode accounts.")
    print("This will allow parallel processing and bypass rate limits.")
    print("Press Enter with empty username to finish adding accounts.")
    print("="*60)
    
    account_num = 1
    while True:
        print(f"\nAccount {account_num}:")
        username = input("Username or Email: ").strip()
        
        if not username:
            break
        
        password = getpass.getpass("Password: ").strip()
        
        if username and password:
            accounts.append({"username": username, "password": password})
            print(f"✅ Account {account_num} added")
            account_num += 1
        else:
            print("❌ Invalid credentials, skipping")
    
    return accounts


def save_state(problem_index, problem_name, status, total_problems, batch_number, successful_submissions, failed_submissions, worker_id=None):
    """Save the current processing state to a JSON file.
    
    Args:
        problem_index: Index of the last processed problem
        problem_name: Name of the last processed problem
        status: Status of the last submission ("success", "failed", "skipped")
        total_problems: Total number of problems
        batch_number: Current batch number
        successful_submissions: Number of successful submissions in current batch
        failed_submissions: Number of failed submissions in current batch
        worker_id: Optional worker ID for multi-account mode (creates separate state files)
    """
    try:
        state = {
            "last_processed_index": problem_index,
            "last_processed_problem": problem_name,
            "last_status": status,
            "total_problems": total_problems,
            "current_batch": batch_number,
            "successful_submissions": successful_submissions,
            "failed_submissions": failed_submissions,
            "timestamp": datetime.now().isoformat(),
            "next_problem_index": problem_index + 1,
            "worker_id": worker_id
        }
        
        # Use worker-specific state file if worker_id is provided
        if worker_id:
            state_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'leetcode_state_{worker_id}.json')
        else:
            state_file_path = STATE_FILE_PATH
        
        with open(state_file_path, 'w', encoding='utf-8') as f:
            json.dump(state, indent=2, fp=f)
        
        if worker_id:
            logging.info(f"[{worker_id}] State saved: {problem_name} (index {problem_index})")
        else:
            logging.info(f"State saved: {problem_name} (index {problem_index})")
        
    except Exception as e:
        logging.error(f"Error saving state: {str(e)}")


def load_state(worker_id=None):
    """Load the processing state from the JSON file.
    
    Args:
        worker_id: Optional worker ID for multi-account mode (loads worker-specific state)
    
    Returns:
        dict: State dictionary or None if no state file exists
    """
    try:
        # Use worker-specific state file if worker_id is provided
        if worker_id:
            state_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'leetcode_state_{worker_id}.json')
        else:
            state_file_path = STATE_FILE_PATH
        
        if os.path.exists(state_file_path):
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            if worker_id:
                logging.info(f"[{worker_id}] State loaded: Last processed {state.get('last_processed_problem', 'Unknown')} (index {state.get('last_processed_index', 0)})")
            else:
                logging.info(f"State loaded: Last processed {state.get('last_processed_problem', 'Unknown')} (index {state.get('last_processed_index', 0)})")
            return state
        else:
            if worker_id:
                logging.info(f"[{worker_id}] No state file found, starting from beginning")
            else:
                logging.info("No state file found, starting from beginning")
            return None
            
    except Exception as e:
        logging.error(f"Error loading state: {str(e)}")
        return None


def clear_state(worker_id=None):
    """Clear the state file.
    
    Args:
        worker_id: Optional worker ID for multi-account mode (clears worker-specific state)
    """
    try:
        # Use worker-specific state file if worker_id is provided
        if worker_id:
            state_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'leetcode_state_{worker_id}.json')
        else:
            state_file_path = STATE_FILE_PATH
        
        if os.path.exists(state_file_path):
            os.remove(state_file_path)
            if worker_id:
                logging.info(f"[{worker_id}] State file cleared")
            else:
                logging.info("State file cleared")
        else:
            if worker_id:
                logging.info(f"[{worker_id}] No state file to clear")
            else:
                logging.info("No state file to clear")
    except Exception as e:
        logging.error(f"Error clearing state: {str(e)}")


def ask_resume_or_restart():
    """Ask user whether to resume from last state or start fresh.
    
    Returns:
        str: "resume" or "restart"
    """
    state = load_state()
    
    if not state:
        return "restart"
    
    last_problem = state.get('last_processed_problem', 'Unknown')
    last_index = state.get('last_processed_index', 0)
    timestamp = state.get('timestamp', 'Unknown')
    next_index = state.get('next_problem_index', 0)
    
    print(f"\n{'='*60}")
    print(f"PREVIOUS SESSION FOUND")
    print(f"{'='*60}")
    print(f"Last processed problem: {last_problem}")
    print(f"Last processed index: {last_index}")
    print(f"Next problem index: {next_index}")
    print(f"Session timestamp: {timestamp}")
    print(f"{'='*60}")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Resume from where you left off")
        print("2. Start fresh from the beginning")
        
        choice = input("Enter your choice (1/2): ").strip()
        
        if choice == "1":
            print("Resuming from last state...")
            return "resume"
        elif choice == "2":
            print("Starting fresh...")
            clear_state()
            return "restart"
        else:
            print("Invalid choice. Please enter 1 or 2.")


def get_credentials():
    """Get user credentials with fallback to defaults if none provided.
    
    Returns:
        tuple: (username, password) - The credentials to use for login
    """
    # Get user credentials
    print("Please enter your LeetCode credentials (press Enter to use default):")
    username = input("Username or Email: ")
    password = getpass.getpass("Password: ")
    
    # Use default credentials if user just presses Enter
    if not username.strip():
        username = DEFAULT_USERNAME
        logging.info(f"Using default username: {DEFAULT_USERNAME}")
    
    if not password.strip():
        password = DEFAULT_PASSWORD
        logging.info("Using default password")
        
    return username, password


def initialize_driver():
    """Initialize and return a configured undetected Chrome WebDriver.
    
    Returns:
        WebDriver: Configured undetected Chrome WebDriver instance
    """
    logging.info("Initializing undetected browser...")
    
    # Create undetected Chrome options
    options = uc.ChromeOptions()
    
    # Add essential options (avoid headless mode for better detection avoidance)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')  # Speed up loading
    options.add_argument('--disable-javascript')  # Optional: disable JS for faster loading
    
    # Create undetected Chrome driver
    driver = uc.Chrome(options=options, version_main=None)
    
    # Set timeouts
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    logging.info("✅ Undetected Chrome browser initialized successfully")
    return driver


def navigate_to_problem(driver, problem_name):
    """
    Navigate to a LeetCode problem page based on the problem name.
    
    Args:
        driver: WebDriver instance
        problem_name: Name of the problem to navigate to (e.g., "01-matrix" from "01-matrix.py")
        
    Returns:
        bool: True if navigation was successful, False otherwise
    """
    try:
        # Construct the problem URL
        problem_url = f"https://leetcode.com/problems/{problem_name}/"
        logging.info(f"Navigating to problem: {problem_url}")
        
        # Navigate to the problem page
        driver.get(problem_url)
        time.sleep(3)  # Allow time for the page to load
        
        # Log the current URL to verify navigation
        current_url = driver.current_url
        logging.info(f"Current URL after navigation: {current_url}")
        
        # Check if we're on the problem page
        if problem_name in current_url:
            logging.info(f"Successfully navigated to problem: {problem_name}")
            return True
        else:
            logging.warning(f"Navigation to problem {problem_name} may have failed. Current URL: {current_url}")
            return False
    except Exception as e:
        logging.error(f"Error navigating to problem {problem_name}: {str(e)}")
        return False


def browse_problems(driver):
    """
    Browse through LeetCode problems in batches of 100 with state management.
    Supports both single-account and multi-account modes.
    
    Args:
        driver: WebDriver instance (used only in single-account mode)
    """
    try:
        # Check if multi-account mode is enabled
        if MULTI_ACCOUNT_CONFIG["enabled"] and MULTI_ACCOUNT_CONFIG["accounts"]:
            return browse_problems_multi_account()
        
        # Original single-account mode
        return browse_problems_single_account(driver)
        
    except Exception as e:
        logging.error(f"Error in browse_problems: {str(e)}")
        print(f"An error occurred while browsing problems: {str(e)}")


def browse_problems_multi_account():
    """Browse problems using multiple accounts in parallel."""
    try:
        # Get account credentials
        accounts = MULTI_ACCOUNT_CONFIG["accounts"]
        
        if not accounts:
            print("🔧 No accounts configured. Trying interactive setup...")
            accounts = get_multi_account_credentials()
            if not accounts:
                print("❌ No accounts provided, falling back to single-account mode")
                return False
        else:
            # Show where accounts came from
            env_accounts = parse_credentials_from_env()
            if env_accounts:
                print(f"🔐 Using {len(accounts)} accounts from environment variables")
                # Mask passwords for security in display
                for i, account in enumerate(accounts, 1):
                    masked_password = '*' * min(len(account['password']), 8)
                    print(f"   Account {i}: {account['username']} (password: {masked_password})")
            else:
                print(f"🔐 Using {len(accounts)} accounts from hardcoded configuration")
                logging.warning("Consider using environment variables for credential security")
        
        # Initialize multi-account manager
        max_workers = min(MULTI_ACCOUNT_CONFIG["max_workers"], len(accounts))
        manager = MultiAccountManager(accounts, max_workers)
        
        try:
            # Initialize drivers
            if not manager.initialize_drivers():
                print("❌ Failed to initialize browser instances")
                return False
            
            # Login to all accounts
            if not manager.login_all_accounts():
                print("❌ Failed to login to accounts")
                return False
            
            # Get problem files
            leet_complete_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Leet_complete")
            problem_files = []
            if os.path.exists(leet_complete_folder):
                for problem_dir in os.listdir(leet_complete_folder):
                    problem_dir_path = os.path.join(leet_complete_folder, problem_dir)
                    if os.path.isdir(problem_dir_path):
                        # Look for Python file with same name as the directory
                        python_file = f"{problem_dir}.py"
                        python_file_path = os.path.join(problem_dir_path, python_file)
                        if os.path.exists(python_file_path):
                            problem_files.append(python_file)
            
            problem_files.sort()
            
            if not problem_files:
                print("No problem files found.")
                return False
            
            total_problems = len(problem_files)
            print(f"Found {total_problems} LeetCode problem files.")
            print(f"Using {max_workers} parallel browser instances")
            
            # Ask user for processing mode
            processing_mode = ask_processing_mode()
            
            if processing_mode == "retry":
                # Retry failed problems mode
                results_file = ask_for_results_file()
                if not results_file:
                    print("❌ No results file provided")
                    return False
                
                # Process failed problems from results file
                success = manager.process_failed_problems_from_results(results_file)
                
            elif processing_mode == "todo":
                # Todo file processing mode
                todo_file = ask_for_todo_file()
                if not todo_file:
                    print("❌ No todo file provided")
                    return False
                
                # Process problems from todo file
                success = manager.process_problems_from_todo_file(todo_file)
                
            else:
                # Regular processing mode
                # Check for existing state
                resume_choice = ask_resume_or_restart()
                start_index = 0
                
                if resume_choice == "resume":
                    state = load_state()
                    if state:
                        start_index = state.get('next_problem_index', 0)
                        if start_index >= total_problems:
                            print("All problems have been processed!")
                            return True
                
                # Process problems in parallel
                print(f"\n🚀 Starting parallel processing from problem {start_index + 1}")
                success = manager.process_problems_parallel(problem_files, start_index)
            
            # If processing was cancelled, return early
            if not success:
                print("❌ Processing was cancelled or failed")
                return False
            
            # Wait for all work to complete (no longer needed with assigned workload)
            # manager.work_queue.join()
            
            # Collect and display results
            results = []
            while not manager.results_queue.empty():
                result_data = manager.results_queue.get()
                # Handle both old format (3 items) and new format (4 items with account_id)
                if len(result_data) == 4:
                    problem_index, problem_name, result, account_id = result_data
                    results.append((problem_index, problem_name, result, account_id))
                else:
                    problem_index, problem_name, result = result_data
                    results.append((problem_index, problem_name, result, "unknown"))
            
            # Sort results by problem index
            results.sort(key=lambda x: x[0])
            
            # Display detailed summary
            successful = sum(1 for _, _, result, _ in results if result == "success")
            failed = sum(1 for _, _, result, _ in results if result == "failed")
            premium = sum(1 for _, _, result, _ in results if result == "PREMIUM_REQUIRED")
            login_required = sum(1 for _, _, result, _ in results if result == "LOGIN_REQUIRED")
            
            print(f"\n{'='*80}")
            print("PARALLEL PROCESSING SUMMARY")
            print(f"{'='*80}")
            print(f"Total processed: {len(results)}")
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"🔒 Premium-only: {premium}")
            if login_required > 0:
                print(f"🔑 Login required: {login_required}")
            print(f"{'='*80}")
            
            # Show results by account
            if results:
                print("\nRESULTS BY ACCOUNT:")
                print("-" * 80)
                account_stats = {}
                for _, _, result, account_id in results:
                    if account_id not in account_stats:
                        account_stats[account_id] = {"success": 0, "failed": 0, "premium": 0, "login": 0}
                    
                    if result == "success":
                        account_stats[account_id]["success"] += 1
                    elif result == "PREMIUM_REQUIRED":
                        account_stats[account_id]["premium"] += 1
                    elif result == "LOGIN_REQUIRED":
                        account_stats[account_id]["login"] += 1
                    else:
                        account_stats[account_id]["failed"] += 1
                
                for account_id, stats in account_stats.items():
                    total = sum(stats.values())
                    print(f"🤖 {account_id}: {total} problems - "
                          f"✅{stats['success']} ❌{stats['failed']} "
                          f"🔒{stats['premium']} 🔑{stats['login']}")
            
            print(f"{'='*80}")
            
            # Export results to file
            if results:
                export_results_to_file(results, max_workers)
            
            return True
            
        finally:
            # Clean up
            manager.cleanup()
            
    except Exception as e:
        logging.error(f"Error in multi-account mode: {str(e)}")
        print(f"Multi-account mode error: {str(e)}")
        return False


def browse_problems_single_account(driver):
    """Original single-account browse problems function."""
    try:
        # Path to the Leet_complete folder
        leet_complete_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Leet_complete")
        logging.info(f"Looking for problem files in: {leet_complete_folder}")
        
        # Get all problem directories and their corresponding Python files
        problem_files = []
        if os.path.exists(leet_complete_folder):
            for problem_dir in os.listdir(leet_complete_folder):
                problem_dir_path = os.path.join(leet_complete_folder, problem_dir)
                if os.path.isdir(problem_dir_path):
                    # Look for Python file with same name as the directory
                    python_file = f"{problem_dir}.py"
                    python_file_path = os.path.join(problem_dir_path, python_file)
                    if os.path.exists(python_file_path):
                        problem_files.append(python_file)
        
        problem_files.sort()  # Sort files alphabetically
        
        if not problem_files:
            logging.warning("No Python files found in the Python folder.")
            print("No problem files found.")
            return
        
        total_problems = len(problem_files)
        logging.info(f"Found {total_problems} problem files.")
        print(f"Found {total_problems} LeetCode problem files.")
        
        # Check for existing state and ask user what to do
        resume_choice = ask_resume_or_restart()
        
        # Determine starting point
        if resume_choice == "resume":
            state = load_state()
            if state:
                start_index = state.get('next_problem_index', 0)
                current_batch = state.get('current_batch', 0)
                successful_submissions = state.get('successful_submissions', 0)
                failed_submissions = state.get('failed_submissions', 0)
                
                # Ensure we don't go beyond the available problems
                if start_index >= total_problems:
                    print("All problems have been processed!")
                    return
                    
                print(f"Resuming from problem {start_index + 1} of {total_problems}")
            else:
                start_index = 0
                current_batch = 0
                successful_submissions = 0
                failed_submissions = 0
        else:
            start_index = 0
            current_batch = 0
            successful_submissions = 0
            failed_submissions = 0
        
        # Process problems in batches of 100
        batch_size = 100
        
        # Calculate which batch we're in based on start_index
        if start_index > 0:
            current_batch = start_index // batch_size
        
        while start_index < total_problems:
            batch_start = current_batch * batch_size
            batch_end = min((current_batch + 1) * batch_size, total_problems)
            
            # If resuming, start from the actual start_index instead of batch_start
            actual_start = max(start_index, batch_start)
            
            print(f"\n{'='*80}")
            print(f"PROCESSING BATCH {current_batch + 1}")
            print(f"Problems {actual_start + 1} to {batch_end} of {total_problems}")
            if actual_start > batch_start:
                print(f"(Resuming from problem {actual_start + 1})")
            print(f"{'='*80}")
            
            # Ask user if they want to process this batch (except for first batch or when resuming)
            if current_batch > 0 and resume_choice != "resume":
                print(f"\nDo you want to process the next {batch_end - actual_start} problems?")
                print("1. Yes, continue with next batch")
                print("2. No, quit")
                
                choice = input("Enter your choice (1/2): ").strip()
                
                if choice == "2":
                    print("Stopping problem processing...")
                    return
                elif choice != "1":
                    print("Invalid choice. Assuming you want to continue...")
            
            # Process problems in this batch
            successful_submissions = 0
            failed_submissions = 0
            premium_required_count = 0
            login_required_count = 0
            
            for i in range(actual_start, batch_end):
                file_name = problem_files[i]
                problem_name = file_name[:-3]  # Remove .py extension
                python_file_path = os.path.join("Leet_complete", problem_name, file_name)
                
                print(f"\n{'='*60}")
                print(f"Problem {i + 1}/{total_problems}: {problem_name}")
                print(f"File: {file_name}")
                print(f"{'='*60}")
                
                # Submit and process the problem
                result = handle_problem_submission(driver, problem_name, python_file_path)
                
                if result == "success":
                    successful_submissions += 1
                    status = "success"
                elif result == "failed":
                    failed_submissions += 1
                    status = "failed"
                elif result == "PREMIUM_REQUIRED":
                    premium_required_count += 1
                    status = "premium_required"
                elif result == "LOGIN_REQUIRED":
                    login_required_count += 1
                    status = "login_required"
                    print("\n⚠️  Multiple login required errors detected.")
                    print("🔄 Consider restarting the script to refresh authentication.")
                    # Don't continue if we have login issues
                    save_state(i, problem_name, status, total_problems, current_batch, successful_submissions, failed_submissions)
                    return
                elif result == "quit":
                    print("User chose to quit.")
                    # Save state before quitting
                    save_state(i, problem_name, "quit", total_problems, current_batch, successful_submissions, failed_submissions)
                    return
                else:
                    failed_submissions += 1
                    status = "unknown"
                
                # Save state after each problem
                save_state(i, problem_name, status, total_problems, current_batch, successful_submissions, failed_submissions)
                
                # Brief pause between submissions to avoid overwhelming the server
                time.sleep(1)
            
            # Print batch summary
            print(f"\n{'='*80}")
            print(f"BATCH {current_batch + 1} SUMMARY")
            print(f"{'='*80}")
            print(f"Total problems processed: {batch_end - actual_start}")
            print(f"Successful submissions: {successful_submissions}")
            print(f"Failed submissions: {failed_submissions}")
            if premium_required_count > 0:
                print(f"Premium-only problems: {premium_required_count}")
            if login_required_count > 0:
                print(f"Login required: {login_required_count}")
            print(f"Remaining problems: {total_problems - batch_end}")
            
            # Check if we have too many premium-only problems
            if premium_required_count > 0:
                print(f"\n💡 Tips for premium-only problems:")
                print(f"   - Consider upgrading to LeetCode Premium")
                print(f"   - These problems will be skipped automatically")
                print(f"   - The script will continue with non-premium problems")
            
            current_batch += 1
            start_index = batch_end  # Update start_index for next batch
            resume_choice = "continue"  # No longer resuming after first batch
        
        print(f"\n🎉 All {total_problems} problems processed!")
        # Clear state file when all problems are complete
        clear_state()
        
    except Exception as e:
        logging.error(f"Error in browse_problems_single_account: {str(e)}")
        print(f"An error occurred while browsing problems: {str(e)}")


def leetcode_login():
    """Main function to handle the LeetCode login process.
    
    This function orchestrates the entire login flow:
    1. Choose between single-account and multi-account modes
    2. Get user credentials (or use defaults)
    3. Initialize the WebDriver(s)
    4. Navigate to the login page(s)
    5. Perform the login(s)
    6. Verify login status
    7. Browse LeetCode problems
    8. Clean up resources
    """
    driver = None
    try:
        # Ask user for processing mode
        multi_account_enabled, max_workers = ask_for_account_mode()
        
        if multi_account_enabled:
            # Multi-account mode
            MULTI_ACCOUNT_CONFIG["enabled"] = True
            MULTI_ACCOUNT_CONFIG["max_workers"] = max_workers
            
            print(f"\n🚀 Starting multi-account mode with {max_workers} parallel instances")
            print("🔧 Using undetected-chromedriver for enhanced stealth")
            print("💡 If you encounter import errors, run: pip install undetected-chromedriver")
            
            # Browse problems in multi-account mode
            success = browse_problems(None)  # Driver not needed in multi-account mode
            
            if success:
                print("\n✅ Multi-account processing completed successfully!")
            else:
                print("\n❌ Multi-account processing encountered errors")
        else:
            # Single account mode (original behavior)
            # Get credentials
            username, password = get_credentials()
            
            # Initialize the webdriver
            driver = initialize_driver()
            
            # Navigate to LeetCode login page
            logging.info(f"Navigating to login page: {LOGIN_URL}")
            driver.get(LOGIN_URL)
            
            # Create a WebDriverWait instance with timeout
            wait = WebDriverWait(driver, PAGE_LOAD_TIMEOUT)
            
            # Perform login
            perform_login(driver, wait, username, password)
            
            # If login is successful, browse problems
            if verify_login_status(driver, wait):
                # Ensure all cookies are loaded before browsing problems
                ensure_all_cookies_loaded(driver)
                browse_problems(driver)
            
            # Keep the browser open until user decides to close
            input("Press Enter to close the browser...")
        
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        # Close the browser if it was initialized
        if driver:
            logging.info("Closing browser...")
            driver.quit()


def perform_login(driver, wait, username, password):
    """Handle the login process and verification.
    
    Args:
        driver: WebDriver instance
        wait: WebDriverWait instance
        username: Username or email for login
        password: Password for login
        
    Raises:
        TimeoutException: If login form elements don't appear in time
        NoSuchElementException: If required elements are not found
    """
    try:
        # Wait for login form to be visible
        logging.info("Waiting for login form...")
        time.sleep(5)
        login_field = wait.until(EC.visibility_of_element_located((By.ID, "id_login")))
        
        # Enter username/email
        login_field.clear()
        login_field.send_keys(username)
        logging.info("Username entered")
        
        # Enter password
        password_field = driver.find_element(By.ID, "id_password")
        password_field.clear()
        password_field.send_keys(password)
        logging.info("Password entered")
        
        # Click login button
        logging.info("Attempting to log in...")
        login_button = driver.find_element(By.ID, "signin_btn")
        login_button.click()
        
        # Wait for login to complete (either success or failure)
        # Using a brief pause to allow the page to respond
        logging.info("Waiting for login response...")
        time.sleep(3)  
        
        # Verify login status
        verify_login_status(driver, wait)
    except TimeoutException as e:
        logging.error(f"Timeout waiting for login form to appear: {str(e)}")
        raise
    except NoSuchElementException as e:
        logging.error(f"Element not found during login: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error during login process: {str(e)}")
        raise


def get_fallback_cookies():
    """Get fallback cookies from the known working curl command.
    
    Returns:
        dict: Dictionary of fallback cookies
    """
    return {
        'cf_clearance': 'SdDmEEI5t8M9W.ZbR_m5LkWm6qErUuEcIH4YHZAnn38-1752336816-1.2.1.1-2I8QZV2vL3waHk3PbVrvvLdxzh.5BG5P51D1kmZDl3EaTJzKf7LDHgL585dEPhja2GE4mWBmcx_QGeh8m_ckvyOpIoeRRjJ4WM9baI0.ReJXr.td6gg.hnn.Z5tE6CjvlDaKfw9ahjwU9MRmlnJsmXA05jo1Somzxt625KgRvlDN4jjS2tkaqySx10qLZnj7xvY2G9gZfrP6lYgtZuAcvv5_XkfCi_8Nv6YSs5jn9FI',
        'ip_check': '(false, "2600:1702:6950:a550:316b:dc25:c772:924")',
        '_dd_s': 'rum=0&expire=1752338154603'
    }


def ensure_all_cookies_loaded(driver):
    """Ensure all necessary cookies are loaded by navigating to key pages.
    
    Args:
        driver: WebDriver instance
    """
    try:
        logging.info("Ensuring all cookies are loaded...")
        
        # First, check if we have cf_clearance cookie
        cookies = driver.get_cookies()
        has_cf_clearance = any(cookie['name'] == 'cf_clearance' for cookie in cookies)
        
        if not has_cf_clearance:
            logging.info("Getting Cloudflare clearance cookie...")
            
            # Navigate to a page that might trigger Cloudflare challenge
            driver.get("https://leetcode.com/problemset/")
            
            # Wait for potential Cloudflare challenge
            max_wait = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Check if we're on a Cloudflare challenge page
                try:
                    if "Just a moment" in driver.title or "Cloudflare" in driver.page_source:
                        time.sleep(2)
                        continue
                    else:
                        # Check if we now have cf_clearance cookie
                        cookies = driver.get_cookies()
                        has_cf_clearance = any(cookie['name'] == 'cf_clearance' for cookie in cookies)
                        if has_cf_clearance:
                            logging.info("cf_clearance cookie obtained")
                            break
                        else:
                            time.sleep(1)
                except Exception:
                    time.sleep(1)
            
            if not has_cf_clearance:
                logging.warning("Could not obtain cf_clearance cookie automatically")
                print("\n⚠️  Cloudflare Challenge Detected!")
                print("Please check the browser window and solve any CAPTCHA or challenge if present.")
                input("Press Enter after you've completed any challenges and the page has loaded...")
                
                # Check again after manual intervention
                cookies = driver.get_cookies()
                has_cf_clearance = any(cookie['name'] == 'cf_clearance' for cookie in cookies)
                if has_cf_clearance:
                    logging.info("cf_clearance cookie obtained")
                else:
                    logging.warning("Still missing cf_clearance cookie")
        
        # Navigate to problemset to get session cookies
        logging.info("Loading session cookies...")
        driver.get("https://leetcode.com/problemset/")
        time.sleep(2)
        
        # Navigate to a problem page to get additional cookies
        driver.get("https://leetcode.com/problems/two-sum/")
        time.sleep(2)
        
        # Go back to problemset
        driver.get("https://leetcode.com/problemset/")
        time.sleep(1)
        
        logging.info("Cookie loading complete")
        
    except Exception as e:
        logging.error(f"Error ensuring cookies are loaded: {str(e)}")


def verify_login_status(driver, wait):
    """Verify if login was successful or not by checking URL changes.
    
    This function checks if the URL has changed to 'leetcode.com' (and is not on the login page)
    which indicates a successful login. If not immediately successful, it will poll every
    15 seconds until the URL changes or the maximum number of attempts is reached.
    
    Args:
        driver: WebDriver instance
        wait: WebDriverWait instance
        
    Returns:
        bool: True if login was successful, False otherwise
    """
    # Check for login success by monitoring URL changes
    attempts = 0
    max_attempts = MAX_LOGIN_ATTEMPTS
    check_interval = LOGIN_CHECK_INTERVAL
    
    while attempts < max_attempts:
        try:
            current_url = driver.current_url
            logging.info(f"Current URL: {current_url}")
            
            # Check if URL has changed to the main LeetCode domain
            if "leetcode.com" in current_url and "/accounts/login" not in current_url:
                logging.info("Login successful! URL has changed to LeetCode main domain.")
                print("Login successful!")
                return True
            
            # If we're still on the login page, check for error messages
            if "/accounts/login" in current_url:
                try:
                    error_message = driver.find_element(By.CLASS_NAME, "alert-error").text
                    logging.error(f"Login failed: {error_message}")
                    print(f"Login failed: {error_message}")
                    return False
                except NoSuchElementException:
                    # No error message found, continue waiting
                    pass
            
            # If this is not the last attempt, wait before checking again
            if attempts < max_attempts - 1:
                logging.info(f"Login status pending. Checking again in {check_interval} seconds...")
                print(f"Waiting for login confirmation... ({attempts + 1}/{max_attempts})")
                time.sleep(check_interval)
        except Exception as e:
            logging.error(f"Error during login verification: {str(e)}")
            print(f"Error checking login status: {str(e)}")
            return False
        
        attempts += 1
    
    # If we've exhausted all attempts and still not successful
    logging.warning("Login verification timed out. Please check the browser manually.")
    print("Login status unknown. Please check the browser.")
    return False


def get_cookies_and_headers(driver):
    """Extract cookies and headers from the Selenium WebDriver for making requests.
    
    Args:
        driver: WebDriver instance
        
    Returns:
        tuple: (cookies_dict, headers_dict) - Cookies and headers for requests
    """
    try:
        # Get all cookies from the browser
        selenium_cookies = driver.get_cookies()
        cookies_dict = {}
        
        for cookie in selenium_cookies:
            cookies_dict[cookie['name']] = cookie['value']
        
        # Check for critical cookies
        critical_cookies = ['cf_clearance', 'csrftoken']
        missing_cookies = []
        for cookie_name in critical_cookies:
            if cookie_name not in cookies_dict:
                missing_cookies.append(cookie_name)
        
        if missing_cookies:
            logging.warning(f"Missing critical cookies: {missing_cookies}")
        
        # Get CSRF token from cookies
        csrf_token = cookies_dict.get('csrftoken', '')
        
        # Get user agent from the browser
        user_agent = driver.execute_script("return navigator.userAgent;")
        
        # Construct headers similar to the curl example
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://leetcode.com',
            'priority': 'u=1, i',
            'referer': driver.current_url,
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': user_agent,
            'x-csrftoken': csrf_token
        }
        
        return cookies_dict, headers
        
    except Exception as e:
        logging.error(f"Error extracting cookies and headers: {str(e)}")
        return {}, {}


def read_python_file_content(file_path):
    """Read the content of a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        str: Content of the Python file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        return None


def get_question_id_from_problem_name(problem_name, cookies_dict, headers):
    """Get question ID from problem name using HTTP request instead of browser navigation.
    
    Args:
        problem_name: Name of the problem
        cookies_dict: Dictionary of cookies
        headers: Dictionary of headers
        
    Returns:
        str: Question ID or None if not found
    """
    try:
        # Construct the problem URL
        problem_url = f"https://leetcode.com/problems/{problem_name}/"
        
        # Make a lightweight HTTP request to get the page
        response = requests.get(
            problem_url,
            headers=headers,
            cookies=cookies_dict,
            timeout=10
        )
        
        if response.status_code != 200:
            logging.error(f"Failed to fetch problem page: {response.status_code}")
            return None
        
        # Parse the response to extract question ID
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find question ID in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string if script.string else ''
            # Look for various patterns
            patterns = [
                r'questionId["\s]*:["\s]*["\']?(\d+)["\']?',
                r'"questionId"["\s]*:["\s]*["\']?(\d+)["\']?',
                r'question_id["\s]*:["\s]*["\']?(\d+)["\']?',
                r'"question_id"["\s]*:["\s]*["\']?(\d+)["\']?',
                r'"id"["\s]*:["\s]*["\']?(\d+)["\']?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    question_id = match.group(1)
                    logging.info(f"Found question ID: {question_id}")
                    return question_id
        
        logging.warning(f"Could not find question ID for problem: {problem_name}")
        return None
        
    except Exception as e:
        logging.error(f"Error getting question ID for {problem_name}: {str(e)}")
        return None


def submit_code_to_leetcode(driver, problem_name, python_file_path):
    """Submit code to LeetCode using the submission API without browser navigation.
    
    Args:
        driver: WebDriver instance
        problem_name: Name of the problem (e.g., "01-matrix")
        python_file_path: Path to the Python solution file
        
    Returns:
        str: Submission ID if successful, None otherwise
    """
    try:
        # Get cookies and headers from the browser
        cookies_dict, headers = get_cookies_and_headers(driver)
        if not cookies_dict:
            return None
        
        # Read the Python file content
        code_content = read_python_file_content(python_file_path)
        if not code_content:
            return None
        
        # Get question ID using HTTP request instead of browser navigation
        question_id = get_question_id_from_problem_name(problem_name, cookies_dict, headers)
        if not question_id:
            return None
        
        # Construct the submission URL
        submit_url = f"https://leetcode.com/problems/{problem_name}/submit/"
        
        # Prepare the payload
        payload = {
            "lang": "python",
            "question_id": question_id,
            "typed_code": code_content
        }
        
        # Retry logic for rate limiting
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Make the submission request
                response = requests.post(
                    submit_url,
                    headers=headers,
                    cookies=cookies_dict,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        submission_id = response_data.get('submission_id')
                        if submission_id:
                            print(f"✅ Code submitted successfully!")
                            print(f"📝 Submission ID: {submission_id}")
                            return submission_id
                        else:
                            print("❌ Submission failed: No submission ID received")
                            return None
                    except json.JSONDecodeError:
                        logging.error("Failed to parse JSON response")
                        print("❌ Submission failed: Invalid response format")
                        
                        # Check if we got redirected to premium/subscription page
                        if "LeetCode Premium" in response.text or "subscribe" in response.text.lower():
                            print("🔒 Problem appears to be premium-only or requires subscription")
                            return "PREMIUM_REQUIRED"
                        
                        # Check if we got redirected to login page
                        if "login" in response.text.lower() or "sign in" in response.text.lower():
                            print("🔑 Session appears to have expired - might need to re-login")
                            return "LOGIN_REQUIRED"
                        
                        # Only print detailed response info for non-premium errors
                        print(f"🔍 Response status: {response.status_code}")
                        print(f"🔍 Response headers: {dict(response.headers)}")
                        # Only show first 200 characters of response for debugging
                        response_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                        print(f"🔍 Response preview: {response_preview}")
                        
                        return None
                elif response.status_code == 429:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                        wait_time = 2 ** (retry_count - 1)
                        print(f"⚠️  Rate limited (429) - retrying in {wait_time} second(s)... (attempt {retry_count}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Submission failed: Rate limited after {max_retries} attempts")
                        return None
                elif response.status_code == 403:
                    logging.error("Submission failed with 403 Forbidden - skipping status check")
                    print("❌ Submission failed with 403 Forbidden")
                    print("⚠️  Skipping status check for this submission")
                    return "403_ERROR"
                else:
                    print(f"❌ Submission failed with status code: {response.status_code}")
                    print(f"🔍 Response content: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                    wait_time = 2 ** (retry_count - 1)
                    print(f"⚠️  Request error - retrying in {wait_time} second(s)... (attempt {retry_count}/{max_retries})")
                    print(f"🔍 Error: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Submission failed after {max_retries} attempts: {str(e)}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error submitting code: {str(e)}")
        return None


def check_submission_status(driver, submission_id):
    """Check the status of a LeetCode submission.
    
    Args:
        driver: WebDriver instance
        submission_id: The submission ID to check
        
    Returns:
        dict: Submission status response or None if failed
    """
    try:
        # Get cookies and headers from the browser
        cookies_dict, headers = get_cookies_and_headers(driver)
        if not cookies_dict:
            return None
        
        # Construct the check URL
        check_url = f"https://leetcode.com/submissions/detail/{submission_id}/check/"
        
        # Make the check request
        response = requests.get(
            check_url,
            headers=headers,
            cookies=cookies_dict,
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                return response_data
            except json.JSONDecodeError:
                return None
        else:
            return None
            
    except Exception as e:
        return None


def wait_for_submission_result(driver, submission_id, max_wait_time=60):
    """Wait for submission result by polling the status endpoint.
    
    Args:
        driver: WebDriver instance
        submission_id: The submission ID to check
        max_wait_time: Maximum time to wait in seconds (default: 60)
        
    Returns:
        dict: Final submission result or None if failed
    """
    import time
    
    start_time = time.time()
    check_interval = 1  # Check every 1 second
    
    print(f"⏳ Waiting for submission result... (max {max_wait_time}s)")
    
    while time.time() - start_time < max_wait_time:
        try:
            status_data = check_submission_status(driver, submission_id)
            
            if status_data is None:
                print("❌ Failed to check submission status")
                return None
            
            state = status_data.get('state', 'UNKNOWN')
            
            if state == 'PENDING':
                # Still pending, wait and check again
                time.sleep(check_interval)
                continue
            elif state == 'STARTED':
                # Still pending, wait and check again
                time.sleep(check_interval)
                continue
            else:
                # Submission is complete, return the result
                print(f"✅ Submission completed with state: {state}")
                return status_data
                
        except Exception as e:
            time.sleep(check_interval)
    
    print(f"⏰ Timeout waiting for submission result after {max_wait_time} seconds")
    return None


def print_submission_result(result):
    """Print the submission result in a formatted way.
    
    Args:
        result: Submission result dictionary
    """
    if not result:
        print("❌ No result to display")
        return
    
    print("\n" + "="*60)
    print("📊 SUBMISSION RESULT")
    print("="*60)
    
    # Basic information
    state = result.get('state', 'UNKNOWN')
    status_msg = result.get('status_msg', 'Unknown')
    lang = result.get('pretty_lang', result.get('lang', 'Unknown'))
    
    print(f"State: {state}")
    print(f"Status: {status_msg}")
    print(f"Language: {lang}")
    
    # Runtime and memory information
    runtime = result.get('display_runtime', result.get('status_runtime', 'N/A'))
    memory = result.get('memory', 'N/A')
    if memory != 'N/A':
        memory_mb = memory / 1000000  # Convert to MB
        print(f"Runtime: {runtime} ms")
        print(f"Memory: {memory_mb:.2f} MB")
    else:
        print(f"Runtime: {runtime}")
        print(f"Memory: {memory}")
    
    # Test case information
    total_testcases = result.get('total_testcases', 0)
    total_correct = result.get('total_correct', 0)
    if total_testcases > 0:
        print(f"Test Cases: {total_correct}/{total_testcases} passed")
    
    # Performance percentiles
    runtime_percentile = result.get('runtime_percentile')
    memory_percentile = result.get('memory_percentile')
    if runtime_percentile is not None:
        print(f"Runtime Percentile: {runtime_percentile}%")
    if memory_percentile is not None:
        print(f"Memory Percentile: {memory_percentile}%")
    
    # Last test case information (if available)
    last_testcase = result.get('last_testcase')
    expected_output = result.get('expected_output')
    if last_testcase and expected_output:
        print(f"\nLast Test Case:")
        print(f"Input: {last_testcase}")
        print(f"Expected: {expected_output}")
    
    # Code output (if available)
    code_output = result.get('code_output')
    if code_output and code_output != "null":
        print(f"\nCode Output: {code_output}")
    
    # Standard output (if available)
    std_output = result.get('std_output')
    if std_output:
        print(f"\nStandard Output: {std_output}")
    
    print("="*60)


def convert_to_markdown(description_text, problem_name):
    """Convert the problem description to markdown format.
    
    Args:
        description_text: The raw description text
        problem_name: Name of the problem
        
    Returns:
        str: Formatted markdown description
    """
    try:
        # Start with the problem title
        markdown_content = f"# {problem_name.replace('-', ' ').title()}\n\n"
        
        # Split the description into sections
        lines = description_text.split('\n')
        
        # Process each line to create proper markdown formatting
        formatted_lines = []
        in_constraints = False
        in_example = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                formatted_lines.append("")
                continue
            
            # Handle example sections
            if line.startswith("Example"):
                in_example = True
                formatted_lines.append(f"## {line}")
                continue
            
            # Handle constraints section
            if "Constraints:" in line:
                in_constraints = True
                formatted_lines.append("## Constraints")
                continue
            
            # Handle input/output in examples
            if line.startswith("Input:") or line.startswith("Output:"):
                formatted_lines.append(f"**{line}**")
                continue
            
            # Handle code-like content (arrays, etc.) - format as inline code
            if line.startswith("mat = ") or line.startswith("[[") or ("[[" in line and "]]" in line):
                formatted_lines.append(f"`{line}`")
                continue
            
            # Handle constraint items (bullets)
            if in_constraints and line.startswith("*"):
                formatted_lines.append(f"- {line[1:].strip()}")
                continue
            
            # Handle note sections
            if line.startswith("Note:"):
                formatted_lines.append(f"## {line}")
                continue
            
            # Handle URLs - convert to markdown links
            if "https://leetcode.com/problems/" in line:
                import re
                url_pattern = r'https://leetcode\.com/problems/[^\s\]]+/?(description/)?'
                urls = re.findall(url_pattern, line)
                for url in urls:
                    # Extract problem name from URL for link text
                    problem_slug = url.split('/problems/')[1].split('/')[0]
                    link_text = problem_slug.replace('-', ' ').title()
                    line = line.replace(url, f"[{link_text}]({url})")
                formatted_lines.append(line)
                continue
            
            # Regular text lines
            if line and not line.startswith("Can you solve this real interview question?"):
                formatted_lines.append(line)
        
        # Join all lines
        markdown_content += "\n".join(formatted_lines)
        
        # Clean up extra whitespace
        markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
        
        return markdown_content
        
    except Exception as e:
        logging.error(f"Error converting to markdown: {str(e)}")
        return description_text


def download_image(image_url, folder_path, image_name, cookies_dict=None, headers=None):
    """Download an image from URL and save it to the specified folder.
    
    Args:
        image_url: URL of the image to download
        folder_path: Path to the folder where image should be saved
        image_name: Name to save the image as
        cookies_dict: Optional cookies dictionary for authenticated requests
        headers: Optional headers dictionary for authenticated requests
        
    Returns:
        str: Path to the saved image or None if failed
    """
    try:
        # Make sure the URL is absolute
        if not image_url.startswith('http'):
            image_url = urljoin('https://leetcode.com', image_url)
        
        # Prepare headers for image download if provided
        img_headers = {}
        if headers:
            img_headers = headers.copy()
            # Update headers for image request
            img_headers.update({
                'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'sec-fetch-dest': 'image',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'cross-site',
                'referer': 'https://leetcode.com/'
            })
            # Remove content-type for image request
            if 'content-type' in img_headers:
                del img_headers['content-type']
        
        # Download the image
        response = requests.get(
            image_url, 
            headers=img_headers if img_headers else None,
            cookies=cookies_dict,
            timeout=30
        )
        response.raise_for_status()
        
        # Create the full path for the image
        image_path = os.path.join(folder_path, image_name)
        
        # Save the image
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"Successfully downloaded image: {image_path}")
        return image_path
        
    except Exception as e:
        logging.error(f"Failed to download image {image_url}: {str(e)}")
        return None


def extract_problem_description(driver, problem_name):
    """Extract the problem description from LeetCode using HTTP requests.
    
    Args:
        driver: WebDriver instance (used only for cookies and headers)
        problem_name: Name of the problem
        
    Returns:
        tuple: (description_text, image_paths) - Description text and list of downloaded image paths
    """
    try:
        # Get cookies and headers from the browser session
        cookies_dict, headers = get_cookies_and_headers(driver)
        if not cookies_dict:
            logging.error("Failed to extract cookies from browser")
            return None, []
        
        # Check for specific cookies that are known to be required
        required_cookies = ['cf_clearance', 'csrftoken']
        for req_cookie in required_cookies:
            if req_cookie not in cookies_dict:
                logging.warning(f"Missing required cookie: {req_cookie}")
                # Try to navigate to LeetCode first to get cookies
                driver.get("https://leetcode.com/problemset/")
                time.sleep(2)
                cookies_dict, headers = get_cookies_and_headers(driver)
                
                # If still missing cf_clearance, use fallback cookies
                if 'cf_clearance' not in cookies_dict:
                    logging.info("Using fallback cookies")
                    fallback_cookies = get_fallback_cookies()
                    for cookie_name, cookie_value in fallback_cookies.items():
                        if cookie_name not in cookies_dict:
                            cookies_dict[cookie_name] = cookie_value
                
                break
        
        # Construct the description URL (using base problem URL like in curl)
        description_url = f"https://leetcode.com/problems/{problem_name}/"
        logging.info(f"Fetching description from: {description_url}")
        
        # Update headers to match the curl request exactly
        html_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=0, i',
            'referer': 'https://leetcode.com/problemset/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        }
        
        # Make the HTTP request to get the description page
        logging.info(f"Fetching description from: {description_url}")
        
        response = requests.get(
            description_url,
            headers=html_headers,
            cookies=cookies_dict,
            timeout=30
        )
        if response.status_code != 200:
            logging.error(f"Failed to fetch description page: {response.status_code}")
            if response.status_code == 403:
                logging.error("403 Forbidden - missing or invalid cookies")
            return None, []
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract description from meta tag (since LeetCode uses client-side rendering)
        description_meta = soup.find('meta', {'name': 'description'})
        if description_meta and description_meta.get('content'):
            description_text = description_meta.get('content')
            logging.info("Successfully extracted description from meta tag")
        else:
            logging.warning("Could not find description in meta tag, trying alternative approach")
            
            # Fallback: Try to find the problem description container in the DOM
            description_selectors = [
                '[data-track-load="description_content"]',
                '.description__24sA',
                '.content__u3I1',
                '.question-content__JfgR',
                '.description',
                '[class*="description"]',
                '[class*="content"]'
            ]
            
            description_element = None
            for selector in description_selectors:
                description_element = soup.select_one(selector)
                if description_element:
                    break
            
            if not description_element:
                logging.warning("Could not find description element, trying alternative approach")
                # Try to find any div with substantial text content
                content_divs = soup.find_all('div')
                for div in content_divs:
                    if div.get_text().strip() and len(div.get_text().strip()) > 100:
                        description_element = div
                        break
            
            if not description_element:
                logging.error("Could not extract problem description")
                return None, []
            
            # Extract text content
            description_text = description_element.get_text(separator='\n', strip=True)
        
        # Create the documentation folder first
        folder_path = create_documentation_folder(problem_name)
        if not folder_path:
            logging.error("Could not create documentation folder")
            return description_text, []
        
        # Find and download images
        image_paths = []
        
        # Extract image URLs from the description text
        import re
        image_url_pattern = r'\[https://assets\.leetcode\.com/[^\]]+\]'
        image_urls = re.findall(image_url_pattern, description_text)
        
        for i, image_url_match in enumerate(image_urls):
            # Extract the actual URL (remove the brackets)
            image_url = image_url_match.strip('[]')
            
            if image_url:
                # Generate a unique name for the image
                image_name = f"image_{i+1}.png"
                
                # Download the image to the problem-specific folder
                image_path = download_image(image_url, folder_path, image_name, cookies_dict, headers)
                if image_path:
                    image_paths.append(image_path)
                    # Replace the image reference in text with markdown image syntax
                    description_text = description_text.replace(image_url_match, f"![Example {i+1}](./{image_name})")
        
        # Also try to find images in the DOM if we had fallback to DOM extraction
        if 'description_element' in locals() and description_element:
            dom_images = description_element.find_all('img')
            
            for i, img in enumerate(dom_images):
                src = img.get('src')
                if src:
                    # Generate a unique name for the image (continue numbering)
                    image_name = f"image_{len(image_paths) + i + 1}.png"
                    
                    # Download the image to the problem-specific folder
                    image_path = download_image(src, folder_path, image_name, cookies_dict, headers)
                    if image_path:
                        image_paths.append(image_path)
                        # Replace the image reference in text with markdown image syntax
                        description_text = description_text.replace(f"[Image {len(image_paths)}]", f"![Example {len(image_paths)}](./{image_name})")
        
        # Convert the description to markdown format
        description_text = convert_to_markdown(description_text, problem_name)
        
        logging.info(f"Successfully extracted description for problem: {problem_name}")
        return description_text, image_paths
        
    except Exception as e:
        logging.error(f"Error extracting problem description: {str(e)}")
        return None, []


def create_documentation_folder(problem_name):
    """Create the documentation folder structure for a problem.
    
    Args:
        problem_name: Name of the problem
        
    Returns:
        str: Path to the created folder
    """
    try:
        # Create the main documentation folder
        base_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Leet_complete")
        os.makedirs(base_folder, exist_ok=True)
        
        # Create the problem-specific folder
        problem_folder = os.path.join(base_folder, problem_name)
        os.makedirs(problem_folder, exist_ok=True)
        
        logging.info(f"Created documentation folder: {problem_folder}")
        return problem_folder
        
    except Exception as e:
        logging.error(f"Error creating documentation folder: {str(e)}")
        return None


def is_problem_already_completed(problem_name):
    """Check if a problem has already been completed and documented.
    
    Args:
        problem_name: Name of the problem
        
    Returns:
        bool: True if problem is already completed, False otherwise
    """
    try:
        # Check if the problem folder exists
        base_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Leet_complete")
        problem_folder = os.path.join(base_folder, problem_name)
        
        if not os.path.exists(problem_folder):
            return False
        
        # Check if both description and result files exist
        desc_file = os.path.join(problem_folder, f"{problem_name}_desc.md")
        result_file = os.path.join(problem_folder, f"{problem_name}_result.txt")
        
        if not os.path.exists(desc_file) or not os.path.exists(result_file):
            return False
        
        # Check if both files are non-empty
        desc_size = os.path.getsize(desc_file)
        result_size = os.path.getsize(result_file)
        
        if desc_size == 0 or result_size == 0:
            logging.warning(f"Empty documentation files found for {problem_name}")
            return False
        
        # Additionally check if the result file indicates success
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result_content = f.read()
                # Check for success indicators in the result file
                if "State: SUCCESS" in result_content or "Status: Accepted" in result_content:
                    logging.info(f"Problem {problem_name} already completed successfully")
                    return True
                else:
                    logging.info(f"Problem {problem_name} has documentation but was not successful")
                    return False
        except Exception as e:
            logging.warning(f"Could not read result file for {problem_name}: {str(e)}")
            return False
        
    except Exception as e:
        logging.error(f"Error checking if problem {problem_name} is completed: {str(e)}")
        return False


def save_problem_description(problem_name, description_text, image_paths):
    """Save the problem description to a markdown file.
    
    Args:
        problem_name: Name of the problem
        description_text: The problem description text (already in markdown format)
        image_paths: List of downloaded image paths
        
    Returns:
        str: Path to the saved description file or None if failed
    """
    try:
        # Create the documentation folder
        folder_path = create_documentation_folder(problem_name)
        if not folder_path:
            return None
        
        # Create the description file path (now as markdown)
        desc_file_path = os.path.join(folder_path, f"{problem_name}_desc.md")
        
        # Write the description to file
        with open(desc_file_path, 'w', encoding='utf-8') as f:
            # The description_text is already in markdown format
            f.write(description_text)
            
            # Add information about downloaded images if any
            if image_paths:
                f.write("\n\n---\n\n")
                f.write("## Images\n\n")
                for i, image_path in enumerate(image_paths, 1):
                    # Show relative path since images are now in the same folder
                    image_name = os.path.basename(image_path)
                    f.write(f"- Image {i}: `{image_name}`\n")
        
        logging.info(f"Successfully saved problem description: {desc_file_path}")
        return desc_file_path
        
    except Exception as e:
        logging.error(f"Error saving problem description: {str(e)}")
        return None


def save_submission_result(problem_name, submission_result, submission_id):
    """Save the submission result to a text file.
    
    Args:
        problem_name: Name of the problem
        submission_result: The submission result dictionary
        submission_id: The submission ID
        
    Returns:
        str: Path to the saved result file or None if failed
    """
    try:
        # Create the documentation folder
        folder_path = create_documentation_folder(problem_name)
        if not folder_path:
            return None
        
        # Create the result file path
        result_file_path = os.path.join(folder_path, f"{problem_name}_result.txt")
        
        # Write the result to file
        with open(result_file_path, 'w', encoding='utf-8') as f:
            f.write(f"Problem: {problem_name}\n")
            f.write(f"Submission ID: {submission_id}\n")
            f.write(f"Submission Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            # Basic information
            state = submission_result.get('state', 'UNKNOWN')
            status_msg = submission_result.get('status_msg', 'Unknown')
            lang = submission_result.get('pretty_lang', submission_result.get('lang', 'Unknown'))
            
            f.write(f"State: {state}\n")
            f.write(f"Status: {status_msg}\n")
            f.write(f"Language: {lang}\n\n")
            
            # Runtime and memory information
            runtime = submission_result.get('display_runtime', submission_result.get('status_runtime', 'N/A'))
            memory = submission_result.get('memory', 'N/A')
            if memory != 'N/A':
                memory_mb = memory / 1000000  # Convert to MB
                f.write(f"Runtime: {runtime} ms\n")
                f.write(f"Memory: {memory_mb:.2f} MB\n\n")
            else:
                f.write(f"Runtime: {runtime}\n")
                f.write(f"Memory: {memory}\n\n")
            
            # Test case information
            total_testcases = submission_result.get('total_testcases', 0)
            total_correct = submission_result.get('total_correct', 0)
            if total_testcases > 0:
                f.write(f"Test Cases: {total_correct}/{total_testcases} passed\n\n")
            
            # Performance percentiles
            runtime_percentile = submission_result.get('runtime_percentile')
            memory_percentile = submission_result.get('memory_percentile')
            if runtime_percentile is not None:
                f.write(f"Runtime Percentile: {runtime_percentile}%\n")
            if memory_percentile is not None:
                f.write(f"Memory Percentile: {memory_percentile}%\n")
            if runtime_percentile is not None or memory_percentile is not None:
                f.write("\n")
            
            # Last test case information (if available)
            last_testcase = submission_result.get('last_testcase')
            expected_output = submission_result.get('expected_output')
            if last_testcase and expected_output:
                f.write("Last Test Case:\n")
                f.write(f"Input: {last_testcase}\n")
                f.write(f"Expected: {expected_output}\n\n")
            
            # Code output (if available)
            code_output = submission_result.get('code_output')
            if code_output and code_output != "null":
                f.write(f"Code Output: {code_output}\n\n")
            
            # Standard output (if available)
            std_output = submission_result.get('std_output')
            if std_output:
                f.write(f"Standard Output: {std_output}\n\n")
            
            # Raw submission data (for debugging)
            f.write("="*60 + "\n")
            f.write("RAW SUBMISSION DATA\n")
            f.write("="*60 + "\n")
            f.write(json.dumps(submission_result, indent=2))
        
        logging.info(f"Successfully saved submission result: {result_file_path}")
        return result_file_path
        
    except Exception as e:
        logging.error(f"Error saving submission result: {str(e)}")
        return None


def document_problem(driver, problem_name, submission_result, submission_id):
    """Complete documentation process for a problem.
    
    Args:
        driver: WebDriver instance
        problem_name: Name of the problem
        submission_result: The submission result dictionary
        submission_id: The submission ID
        
    Returns:
        bool: True if documentation was successful, False otherwise
    """
    try:
        print(f"\n📝 Starting documentation for problem: {problem_name}")
        
        # Extract and save problem description
        print("📖 Extracting problem description...")
        description_text, image_paths = extract_problem_description(driver, problem_name)
        
        if description_text:
            desc_file_path = save_problem_description(problem_name, description_text, image_paths)
            if desc_file_path:
                print(f"✅ Problem description saved: {desc_file_path}")
            else:
                print("❌ Failed to save problem description")
        else:
            print("❌ Failed to extract problem description")
        
        # Save submission result
        print("📊 Saving submission result...")
        result_file_path = save_submission_result(problem_name, submission_result, submission_id)
        
        if result_file_path:
            print(f"✅ Submission result saved: {result_file_path}")
            print(f"📁 Documentation folder: Leet_complete/{problem_name}/")
            return True
        else:
            print("❌ Failed to save submission result")
            return False
            
    except Exception as e:
        logging.error(f"Error in documentation process: {str(e)}")
        print(f"❌ Documentation failed: {str(e)}")
        return False


def handle_problem_submission(driver, problem_name, python_file_path):
    """Handle the complete submission process for a problem (simplified for batch processing).
    
    Args:
        driver: WebDriver instance
        problem_name: Name of the problem
        python_file_path: Path to the Python solution file
        
    Returns:
        str: "success", "failed", or "quit"
    """
    try:
        print(f"🔄 Processing: {problem_name}")
        
        # Check if problem is already completed
        if is_problem_already_completed(problem_name):
            print(f"✅ Problem {problem_name} already completed successfully - skipping")
            return "success"
        
        # Submit the code
        submission_id = submit_code_to_leetcode(driver, problem_name, python_file_path)
        
        if submission_id == "403_ERROR":
            # Handle 403 error - skip status check
            print("⚠️  Received 403 error - skipping this problem")
            return "failed"
        
        elif submission_id == "PREMIUM_REQUIRED":
            # Handle premium-only problem
            print("🔒 Problem requires premium subscription - skipping")
            return "PREMIUM_REQUIRED"
        
        elif submission_id == "LOGIN_REQUIRED":
            # Handle login required
            print("🔑 Authentication issue detected - skipping")
            return "LOGIN_REQUIRED"
        
        elif submission_id:
            print(f"✅ Submitted (ID: {submission_id})")
            
            # Check submission status
            print("🔄 Checking status...")
            result = wait_for_submission_result(driver, submission_id)
            
            if result:
                state = result.get('state', 'UNKNOWN')
                status_msg = result.get('status_msg', 'Unknown')
                print(f"📊 Result: {state} - {status_msg}")
                
                # Document successful submissions
                if state == 'SUCCESS':
                    print("📝 Documenting...")
                    document_success = document_problem(driver, problem_name, result, submission_id)
                    if document_success:
                        print("✅ Documented successfully!")
                        return "success"
                    else:
                        print("⚠️  Documentation failed, but submission was successful")
                        return "success"
                else:
                    print(f"⚠️  Submission not successful: {state}")
                    return "failed"
            else:
                print("❌ Failed to get submission result")
                return "failed"
        else:
            print("❌ Submission failed")
            return "failed"
            
    except Exception as e:
        logging.error(f"Error in handle_problem_submission: {str(e)}")
        print(f"❌ Error processing {problem_name}: {str(e)}")
        return "failed"


def export_results_to_file(results, max_workers):
    """Export processing results to a file for analysis."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leetcode_results_{timestamp}.json"
        
        # Prepare data for export
        export_data = {
            "session_info": {
                "timestamp": timestamp,
                "total_problems": len(results),
                "parallel_workers": max_workers,
                "processing_mode": "multi-account"
            },
            "summary": {
                "successful": sum(1 for _, _, result, _ in results if result == "success"),
                "failed": sum(1 for _, _, result, _ in results if result == "failed"),
                "premium_required": sum(1 for _, _, result, _ in results if result == "PREMIUM_REQUIRED"),
                "login_required": sum(1 for _, _, result, _ in results if result == "LOGIN_REQUIRED")
            },
            "results": []
        }
        
        # Add individual results
        for problem_index, problem_name, result, account_id in results:
            export_data["results"].append({
                "problem_index": problem_index,
                "problem_name": problem_name,
                "result": result,
                "account_id": account_id
            })
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Results exported to: {filename}")
        print(f"   Use this file to analyze performance and track progress")
        
    except Exception as e:
        logging.error(f"Error exporting results: {str(e)}")
        print(f"⚠️  Could not export results: {str(e)}")


def show_multi_account_setup_instructions():
    """Show instructions for setting up multi-account mode."""
    print("\n" + "="*80)
    print("📖 MULTI-ACCOUNT SETUP INSTRUCTIONS")
    print("="*80)
    print("To use multi-account mode, you have three options:")
    print()
    print("OPTION 1: Environment Variables (RECOMMENDED - Most Secure)")
    print("- Set the LEET_CREDS environment variable")
    print("- Format: user1:pass1,user2:pass2,user3:pass3")
    print("- Example commands:")
    print("  Linux/Mac: export LEET_CREDS='user1@example.com:password1,user2@example.com:password2'")
    print("  Windows:   set LEET_CREDS=user1@example.com:password1,user2@example.com:password2")
    print("- Or create a .env file in the project directory:")
    print("  LEET_CREDS=user1@example.com:password1,user2@example.com:password2")
    print()
    print("OPTION 2: Interactive Setup (For testing/one-time use)")
    print("- Choose multi-account mode when prompted")
    print("- Enter credentials for each account interactively")
    print("- Accounts are used for this session only")
    print()
    print("OPTION 3: Hardcoded Configuration (Not recommended)")
    print("- Edit the hardcoded_accounts list in get_accounts_from_config()")
    print("- Add your accounts to the list")
    print("- Example:")
    print('  hardcoded_accounts = [')
    print('      {"username": "user1@example.com", "password": "password1"},')
    print('      {"username": "user2@example.com", "password": "password2"},')
    print('  ]')
    print()
    print("🔐 SECURITY BEST PRACTICES:")
    print("- Use environment variables (Option 1) for production")
    print("- Never commit credentials to version control")
    print("- Use strong, unique passwords for each account")
    print("- Consider using app passwords if available")
    print("- Each account should be a legitimate LeetCode account")
    print("- Respect LeetCode's terms of service")
    print()
    print("🚀 BENEFITS:")
    print("- 3-5x faster processing")
    print("- Bypass individual account rate limits")
    print("- Parallel submission and result checking")
    print("- Independent browser sessions")
    print("- Secure credential management")
    print()
    print("💡 EXAMPLE .env FILE:")
    print("LEET_CREDS=john.doe@email.com:mypassword123,jane.smith@email.com:securepass456")
    print("="*80)


def ask_processing_mode():
    """Ask user for processing mode: regular, retry failed problems, or from todo file.
    
    Returns:
        str: "regular", "retry", or "todo"
    """
    print("\n" + "="*60)
    print("PROCESSING MODE SELECTION")
    print("="*60)
    print("Choose what you want to process:")
    print("1. Regular Processing (Process all problems)")
    print("2. Retry Failed Problems (From results file)")
    print("3. Process Problems from Todo File (From to_do.json)")
    print("="*60)
    
    while True:
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            print("✅ Selected: Regular Processing")
            return "regular"
        elif choice == "2":
            print("✅ Selected: Retry Failed Problems")
            return "retry"
        elif choice == "3":
            print("✅ Selected: Process Problems from Todo File")
            return "todo"
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


def ask_for_results_file():
    """Ask user for results file path and validate it exists.
    
    Returns:
        str: Path to results file or None if invalid
    """
    print("\n" + "="*60)
    print("RESULTS FILE SELECTION")
    print("="*60)
    print("Please provide the path to your results JSON file.")
    print("Example: leetcode_results_20250712_122643.json")
    print("="*60)
    
    # List available results files in current directory
    import glob
    results_files = glob.glob("leetcode_results_*.json")
    
    if results_files:
        print("\n📁 Available results files in current directory:")
        for i, file in enumerate(results_files, 1):
            print(f"{i}. {file}")
        print(f"{len(results_files) + 1}. Enter custom path")
        print("="*60)
        
        while True:
            choice = input(f"Select file (1-{len(results_files) + 1}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(results_files):
                    selected_file = results_files[choice_num - 1]
                    print(f"✅ Selected: {selected_file}")
                    return selected_file
                elif choice_num == len(results_files) + 1:
                    break  # Go to custom path input
                else:
                    print(f"❌ Please enter a number between 1 and {len(results_files) + 1}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    # Custom path input
    while True:
        file_path = input("Enter results file path (or 'cancel' to abort): ").strip()
        
        if file_path.lower() == 'cancel':
            return None
        
        if not file_path:
            print("❌ Please enter a file path")
            continue
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        
        if not file_path.endswith('.json'):
            print("❌ Please provide a JSON file")
            continue
        
        print(f"✅ Selected: {file_path}")
        return file_path


def ask_for_todo_file():
    """Ask user for todo file path and validate it exists.
    
    Returns:
        str: Path to todo file or None if invalid
    """
    print("\n" + "="*60)
    print("TODO FILE SELECTION")
    print("="*60)
    print("Please provide the path to your todo JSON file.")
    print("Example: to_do.json")
    print("Expected format: {\"problems\": [\"problem-name-1\", \"problem-name-2\", ...]}")
    print("="*60)
    
    # List available todo files in current directory
    import glob
    todo_files = glob.glob("*to_do*.json") + glob.glob("*todo*.json")
    
    if todo_files:
        print("\n📁 Available todo files in current directory:")
        for i, file in enumerate(todo_files, 1):
            print(f"{i}. {file}")
        print(f"{len(todo_files) + 1}. Enter custom path")
        print("="*60)
        
        while True:
            choice = input(f"Select file (1-{len(todo_files) + 1}): ").strip()
            
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(todo_files):
                    selected_file = todo_files[choice_num - 1]
                    print(f"✅ Selected: {selected_file}")
                    return selected_file
                elif choice_num == len(todo_files) + 1:
                    break  # Go to custom path input
                else:
                    print(f"❌ Please enter a number between 1 and {len(todo_files) + 1}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    # Custom path input
    while True:
        file_path = input("Enter todo file path (or 'cancel' to abort): ").strip()
        
        if file_path.lower() == 'cancel':
            return None
        
        if not file_path:
            print("❌ Please enter a file path")
            continue
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        
        if not file_path.endswith('.json'):
            print("❌ Please provide a JSON file")
            continue
        
        print(f"✅ Selected: {file_path}")
        return file_path


def ask_for_account_mode():
    """Ask user for account mode and return configuration."""
    show_multi_account_setup_instructions()
    
    print("\n" + "="*60)
    print("LEETCODE AUTOMATION MODE SELECTION")
    print("="*60)
    print("Choose your processing mode:")
    print("1. Single Account Mode (Original)")
    print("2. Multi-Account Mode (Parallel Processing)")
    print("3. Show setup instructions again")
    print("="*60)
    
    while True:
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            print("✅ Selected: Single Account Mode")
            return False, 1
        elif choice == "2":
            print("✅ Selected: Multi-Account Mode")
            
            # Ask for number of workers
            while True:
                try:
                    max_workers = input(f"Number of parallel instances (1-5, default 3): ").strip()
                    if not max_workers:
                        max_workers = 3
                    else:
                        max_workers = int(max_workers)
                    
                    if 1 <= max_workers <= 5:
                        return True, max_workers
                    else:
                        print("❌ Please enter a number between 1 and 5")
                except ValueError:
                    print("❌ Please enter a valid number")
        elif choice == "3":
            show_multi_account_setup_instructions()
            continue
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    try:
        leetcode_login()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        logging.exception("Unexpected error in main execution:")
        sys.exit(1)