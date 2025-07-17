#!/usr/bin/env python3
"""
Analyze LeetCode Problems with Gemini AI

This script goes through all problems in Leet_complete directory and uses
Google's Gemini AI to analyze the problem description and solution code
to extract insights about data structures, algorithms, and problem categories.

Features:
- Single problem analysis and batch processing
- Smart detection of existing analyses with skip/rerun options
- Automatic filtering of failed problems (from failed_problems.json)
- Performance testing across different batch sizes
- Multiple solution support (data_structures, algorithm_technique, key_insights as lists)
- Comprehensive analysis including data structures, algorithms, and complexity
- Built-in rate limiting (15 requests per minute) to respect API limits
- Intelligent request spacing for optimal API usage
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
import argparse
from datetime import datetime
from collections import deque

# Configure Gemini AI
# You need to set your API key either as an environment variable or directly here
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Set this environment variable
# Alternatively, you can set it directly (not recommended for security):
# GEMINI_API_KEY = "your-api-key-here"

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY environment variable not set")
    print("Please set it using: export GEMINI_API_KEY='your-api-key'")
    sys.exit(1)

# Configure the API
genai.configure(api_key=GEMINI_API_KEY)

# Available problem categories
PROBLEM_CATEGORIES = [
    "Arrays & Hashing",
    "Two Pointers", 
    "Binary Search",
    "Stack",
    "Sliding Window",
    "Linked List",
    "Trees",
    "Tries",
    "Heap / Priority Queue",
    "Backtracking",
    "Graphs",
    "1-D Dynamic Programming",
    "Intervals",
    "Advanced Graphs", 
    "2-D Dynamic Programming",
    "Greedy",
    "Math & Geometry",
    "Bit Manipulation"
]

class APIRateLimiter:
    """
    Rate limiter for Gemini API calls to ensure we don't exceed 15 requests per minute.
    """
    def __init__(self, max_requests_per_minute: int = 15):
        self.max_requests = max_requests_per_minute
        self.request_times = deque()
        self.min_interval = 60.0 / max_requests_per_minute  # Minimum seconds between requests
        
    def wait_if_needed(self):
        """
        Wait if necessary to respect rate limits.
        """
        current_time = time.time()
        
        # Remove request times older than 1 minute
        while self.request_times and current_time - self.request_times[0] >= 60:
            self.request_times.popleft()
        
        # Check if we're at the limit
        if len(self.request_times) >= self.max_requests:
            # Need to wait until the oldest request is more than 1 minute old
            oldest_request = self.request_times[0]
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                print(f"⏱️  Rate limit: waiting {wait_time:.1f}s to respect 15 requests/minute limit...")
                time.sleep(wait_time)
                current_time = time.time()
                # Clean up old requests again after waiting
                while self.request_times and current_time - self.request_times[0] >= 60:
                    self.request_times.popleft()
        
        # Also ensure minimum interval between requests (for smoother distribution)
        if self.request_times:
            time_since_last = current_time - self.request_times[-1]
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                print(f"⏱️  Smoothing requests: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                current_time = time.time()
        
        # Record this request
        self.request_times.append(current_time)
        
    def get_current_rate_info(self) -> str:
        """
        Get current rate limiting information for display.
        """
        current_time = time.time()
        # Clean up old requests
        while self.request_times and current_time - self.request_times[0] >= 60:
            self.request_times.popleft()
        
        requests_in_last_minute = len(self.request_times)
        remaining_requests = self.max_requests - requests_in_last_minute
        
        if self.request_times:
            time_since_last = current_time - self.request_times[-1]
            next_available = max(0, self.min_interval - time_since_last)
        else:
            next_available = 0
            
        return f"📊 Rate limit status: {requests_in_last_minute}/{self.max_requests} requests in last minute, {remaining_requests} remaining, next available in {next_available:.1f}s"

# Global rate limiter instance
rate_limiter = APIRateLimiter(max_requests_per_minute=15)

def load_failed_problems() -> set:
    """
    Load the list of failed problems from failed_problems.json.
    
    Returns:
        set: Set of failed problem names across all failure categories
    """
    try:
        script_dir = Path(__file__).parent
        failed_problems_file = script_dir / "failed_problems.json"
        
        if not failed_problems_file.exists():
            print("⚠️  failed_problems.json not found - will analyze all problems")
            return set()
        
        with open(failed_problems_file, 'r', encoding='utf-8') as f:
            failed_data = json.load(f)
        
        # Combine all failed problems from all categories
        all_failed = set()
        for category, problems in failed_data.items():
            all_failed.update(problems)
        
        print(f"📋 Loaded {len(all_failed)} failed problems from failed_problems.json")
        return all_failed
        
    except Exception as e:
        print(f"❌ Error loading failed_problems.json: {str(e)}")
        return set()

def check_analysis_exists(problem_name: str, output_dir: Path) -> bool:
    """
    Check if analysis already exists for a problem.
    
    Args:
        problem_name: Name of the problem
        output_dir: Directory where analyses are saved
        
    Returns:
        bool: True if analysis file exists, False otherwise
    """
    analysis_file = output_dir / f"{problem_name}_analysis.json"
    return analysis_file.exists()

def get_existing_analyses(problem_dirs: List[Path], output_dir: Path) -> Tuple[List[Path], List[Path]]:
    """
    Separate problems into those with existing analyses and those without.
    
    Args:
        problem_dirs: List of problem directory paths
        output_dir: Directory where analyses are saved
        
    Returns:
        Tuple of (problems_with_analysis, problems_without_analysis)
    """
    with_analysis = []
    without_analysis = []
    
    for problem_dir in problem_dirs:
        if check_analysis_exists(problem_dir.name, output_dir):
            with_analysis.append(problem_dir)
        else:
            without_analysis.append(problem_dir)
    
    return with_analysis, without_analysis

def ask_about_existing_analyses(problems_with_analysis: List[Path]) -> bool:
    """
    Ask user whether to skip or rerun existing analyses.
    
    Args:
        problems_with_analysis: List of problems that already have analyses
        
    Returns:
        bool: True to rerun existing analyses, False to skip them
    """
    if not problems_with_analysis:
        return False  # No existing analyses to worry about
    
    print(f"\n🔍 Found {len(problems_with_analysis)} problems with existing analyses:")
    
    # Show first few examples
    example_count = min(5, len(problems_with_analysis))
    for i, problem_dir in enumerate(problems_with_analysis[:example_count]):
        print(f"   ✅ {problem_dir.name}")
    
    if len(problems_with_analysis) > example_count:
        print(f"   ... and {len(problems_with_analysis) - example_count} more")
    
    print(f"\n❓ What would you like to do with these {len(problems_with_analysis)} already-analyzed problems?")
    print("   1. Skip them (faster, use existing results)")
    print("   2. Rerun analysis (will overwrite existing results)")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            print("✅ Will skip existing analyses")
            return False
        elif choice == "2":
            print("🔄 Will rerun existing analyses")
            return True
        else:
            print("❌ Please enter 1 or 2")

def filter_problems_by_user_choice(problem_dirs: List[Path], output_dir: Path) -> List[Path]:
    """
    Filter problems based on user's choice about existing analyses and failed problems.
    
    Args:
        problem_dirs: List of all problem directories
        output_dir: Directory where analyses are saved
        
    Returns:
        List of problems to analyze
    """
    # First, filter out failed problems
    failed_problems = load_failed_problems()
    
    if failed_problems:
        # Remove failed problems from the list
        filtered_dirs = []
        skipped_failed = []
        
        for problem_dir in problem_dirs:
            if problem_dir.name in failed_problems:
                skipped_failed.append(problem_dir.name)
            else:
                filtered_dirs.append(problem_dir)
        
        if skipped_failed:
            print(f"🚫 Skipping {len(skipped_failed)} failed problems:")
            # Show first few examples
            example_count = min(5, len(skipped_failed))
            for i, problem_name in enumerate(skipped_failed[:example_count]):
                print(f"   ❌ {problem_name}")
            if len(skipped_failed) > example_count:
                print(f"   ... and {len(skipped_failed) - example_count} more")
        
        problem_dirs = filtered_dirs
    
    # Now handle existing analyses
    with_analysis, without_analysis = get_existing_analyses(problem_dirs, output_dir)
    
    # If no existing analyses, return all problems (already filtered for failed ones)
    if not with_analysis:
        print(f"📊 No existing analyses found. Will analyze all {len(problem_dirs)} problems.")
        return problem_dirs
    
    # Ask user what to do with existing analyses
    rerun_existing = ask_about_existing_analyses(with_analysis)
    
    if rerun_existing:
        # User wants to rerun everything
        print(f"📊 Will analyze all {len(problem_dirs)} problems (including {len(with_analysis)} reruns)")
        return problem_dirs
    else:
        # User wants to skip existing ones
        print(f"📊 Will analyze {len(without_analysis)} new problems (skipping {len(with_analysis)} existing)")
        return without_analysis


def create_simplified_retry_prompt(original_prompt: str, missing_fields: List[str]) -> str:
    """
    Create a simplified retry prompt focusing on missing fields.
    
    Args:
        original_prompt: The original prompt that failed
        missing_fields: List of fields that were missing in the response
        
    Returns:
        str: Simplified prompt focusing on missing fields
    """
    # Extract problem description and solution from original prompt
    lines = original_prompt.split('\n')
    desc_start = -1
    desc_end = -1
    sol_start = -1
    sol_end = -1
    
    for i, line in enumerate(lines):
        if '**Problem Description:**' in line:
            desc_start = i + 1
        elif '**Python Solution:**' in line:
            desc_end = i - 1
            sol_start = i + 1
        elif 'CRITICAL:' in line or 'REQUIRED JSON' in line:
            sol_end = i - 1
            break
    
    if desc_start > 0 and sol_start > 0:
        description = '\n'.join(lines[desc_start:desc_end])
        solution = '\n'.join(lines[sol_start:sol_end])
    else:
        # Fallback - use simplified content
        description = "Problem description from previous context"
        solution = "Solution code from previous context"
    
    # Create field-specific requirements
    field_requirements = {
        'problem_summary_simple': "simple explanation under 30 words",
        'problem_summary_technical': "technical summary under 35 words", 
        'data_structures': 'list of lists like [["array", "hashmap"]]',
        'category': f'one of: {", ".join(PROBLEM_CATEGORIES[:5])}...',  # Shortened list
        'algorithm_technique': 'list like ["two pointers technique"]',
        'time_complexity': 'list like ["O(n)"]',
        'space_complexity': 'list like ["O(1)"]',
        'key_insights': 'list of lists like [["insight1", "insight2"]]',
        'difficulty_level': '"Easy", "Medium", or "Hard"'
    }
    
    missing_requirements = []
    for field in missing_fields:
        if field in field_requirements:
            missing_requirements.append(f'"{field}": {field_requirements[field]}')
    
    prompt = f"""SIMPLIFIED ANALYSIS REQUEST

The previous analysis was incomplete. Please provide ONLY the missing fields in valid JSON format.

Missing fields needed:
{chr(10).join(f"- {req}" for req in missing_requirements)}

Respond with ONLY a JSON object containing these {len(missing_fields)} missing fields:

{{
    {','.join(f'"{field}": "your_{field}_value"' for field in missing_fields)}
}}

Keep it simple and direct. Use standard values."""
    
    return prompt


def create_analysis_prompt(problem_description: str, solution_code: str) -> str:
    """
    Create an improved analysis prompt for Gemini.
    
    Args:
        problem_description: The problem description in markdown
        solution_code: The Python solution code
        
    Returns:
        str: Formatted prompt for Gemini
    """
    prompt = f"""You are an expert LeetCode problem analyzer. Analyze the following problem and solution, then provide a comprehensive analysis.

**Problem Description:**
```
{problem_description}
```

**Python Solution:**
```python
{solution_code}
```

CRITICAL: You MUST provide a response in STRICT JSON format with ALL the following fields. Missing ANY field will cause the analysis to fail.

**REQUIRED JSON STRUCTURE (ALL FIELDS MANDATORY):**
```json
{{
    "data_structures": [["list of data structures for solution 1"], ["list for solution 2"], ...],
    "category": "single category from the provided list",
    "algorithm_technique": ["algorithm/technique for solution 1", "algorithm/technique for solution 2", ...],
    "problem_summary_simple": "simple explanation of what the problem asks (under 30 words)",
    "problem_summary_technical": "technical summary focusing on data structures and algorithms (under 35 words)",
    "time_complexity": ["Big O time complexity for solution 1", "Big O time complexity for solution 2", ...],
    "space_complexity": ["Big O space complexity for solution 1", "Big O space complexity for solution 2", ...],
    "key_insights": [["insights for solution 1"], ["insights for solution 2"], ...],
    "difficulty_level": "Easy/Medium/Hard based on the solution complexity"
}}
```

**EXAMPLE RESPONSE FORMAT:**
```json
{{
    "data_structures": [["array", "hashmap"]],
    "category": "Arrays & Hashing",
    "algorithm_technique": ["two pointers with hashmap lookup"],
    "problem_summary_simple": "Find two numbers in array that add up to target value",
    "problem_summary_technical": "Use hashmap for O(1) lookup with single pass through array",
    "time_complexity": ["O(n)"],
    "space_complexity": ["O(n)"],
    "key_insights": [["use hashmap for O(1) lookup", "two pointers avoid nested loops", "complement calculation is key optimization"]],
    "difficulty_level": "Easy"
}}
```

**DETAILED FIELD REQUIREMENTS:**

1. **data_structures** (MANDATORY): List of lists containing data structures used
   - Even for single solution: [["array", "hashmap"]]
   - For multiple solutions: [["array"], ["hashmap", "set"]]

2. **category** (MANDATORY): Choose EXACTLY ONE from: {', '.join(PROBLEM_CATEGORIES)}

3. **algorithm_technique** (MANDATORY): List of technique descriptions
   - Each technique under 25 words
   - Even for single solution: ["two pointers technique"]

4. **problem_summary_simple** (MANDATORY): Plain English explanation
   - Under 30 words
   - What the problem asks in simple terms
   - Example: "Find two numbers that add up to target"

5. **problem_summary_technical** (MANDATORY): Technical algorithm focus
   - Under 35 words
   - Focus on data structures and algorithms used
   - Example: "Use hashmap for O(1) lookup with single array pass"

6. **time_complexity** (MANDATORY): List of Big O time complexities
   - Standard Big O notation: ["O(n)", "O(log n)", "O(n²)"]

7. **space_complexity** (MANDATORY): List of Big O space complexities
   - Standard Big O notation: ["O(1)", "O(n)", "O(log n)"]

8. **key_insights** (MANDATORY): List of lists with insights
   - Each solution has 2-3 key insights
   - Format: [["insight1", "insight2", "insight3"]]

9. **difficulty_level** (MANDATORY): One of "Easy", "Medium", or "Hard"

**VALIDATION CHECKLIST - VERIFY ALL BEFORE RESPONDING:**
✓ All 9 fields are present
✓ problem_summary_simple exists and is under 30 words
✓ problem_summary_technical exists and is under 35 words
✓ category is from the provided list
✓ All arrays use proper list format
✓ JSON is valid and properly formatted

RESPOND ONLY with the JSON object. NO explanations, NO markdown blocks, NO additional text."""
    
    return prompt


def create_batch_analysis_prompt(problems_data: List[Tuple[str, str, str]]) -> str:
    """
    Create a batch analysis prompt for multiple problems.
    
    Args:
        problems_data: List of tuples (problem_name, description, solution_code)
        
    Returns:
        str: Formatted batch prompt for Gemini
    """
    problems_section = ""
    for i, (problem_name, description, solution_code) in enumerate(problems_data, 1):
        problems_section += f"""
**PROBLEM {i}: {problem_name}**

Problem Description:
```
{description}
```

Python Solution:
```python
{solution_code}
```

---
"""
    
    prompt = f"""You are an expert LeetCode problem analyzer. Analyze ALL {len(problems_data)} problems below and provide comprehensive analysis for each.

{problems_section}

CRITICAL: You MUST provide a response in STRICT JSON ARRAY format with ALL required fields for EVERY problem. Missing ANY field for ANY problem will cause the analysis to fail.

**REQUIRED JSON ARRAY STRUCTURE (ALL FIELDS MANDATORY FOR EACH PROBLEM):**
```json
[
    {{
        "problem_name": "exact problem name",
        "data_structures": [["list of data structures for solution 1"], ["list for solution 2"], ...],
        "category": "single category from the provided list",
        "algorithm_technique": ["algorithm/technique for solution 1", "algorithm/technique for solution 2", ...],
        "problem_summary_simple": "simple explanation of what the problem asks (under 30 words)",
        "problem_summary_technical": "technical summary focusing on data structures and algorithms (under 35 words)",
        "time_complexity": ["Big O time complexity for solution 1", "Big O time complexity for solution 2", ...],
        "space_complexity": ["Big O space complexity for solution 1", "Big O space complexity for solution 2", ...],
        "key_insights": [["insights for solution 1"], ["insights for solution 2"], ...],
        "difficulty_level": "Easy/Medium/Hard based on the solution complexity"
    }},
    ... (repeat for all {len(problems_data)} problems)
]
```

**EXAMPLE RESPONSE (SHOWING PROPER STRUCTURE):**
```json
[
    {{
        "problem_name": "two-sum",
        "data_structures": [["array", "hashmap"]],
        "category": "Arrays & Hashing",
        "algorithm_technique": ["two pointers with hashmap lookup"],
        "problem_summary_simple": "Find two numbers in array that add up to target value",
        "problem_summary_technical": "Use hashmap for O(1) lookup with single pass through array",
        "time_complexity": ["O(n)"],
        "space_complexity": ["O(n)"],
        "key_insights": [["use hashmap for O(1) lookup", "two pointers avoid nested loops", "complement calculation is key optimization"]],
        "difficulty_level": "Easy"
    }},
    {{
        "problem_name": "valid-parentheses",
        "data_structures": [["stack"]],
        "category": "Stack",
        "algorithm_technique": ["stack-based matching"],
        "problem_summary_simple": "Check if parentheses are properly balanced and nested",
        "problem_summary_technical": "Use stack to track opening brackets and match with closing ones",
        "time_complexity": ["O(n)"],
        "space_complexity": ["O(n)"],
        "key_insights": [["stack naturally handles nested structure", "early termination on mismatch", "empty stack indicates balanced"]],
        "difficulty_level": "Easy"
    }}
]
```

**DETAILED FIELD REQUIREMENTS FOR EACH PROBLEM:**

1. **problem_name** (MANDATORY): Use EXACT name provided (e.g., "1-bit-and-2-bit-characters")

2. **data_structures** (MANDATORY): List of lists containing data structures used
   - Even for single solution: [["array", "hashmap"]]
   - For multiple solutions: [["array"], ["hashmap", "set"]]

3. **category** (MANDATORY): Choose EXACTLY ONE from: {', '.join(PROBLEM_CATEGORIES)}

4. **algorithm_technique** (MANDATORY): List of technique descriptions
   - Each technique under 25 words
   - Even for single solution: ["two pointers technique"]

5. **problem_summary_simple** (MANDATORY): Plain English explanation
   - Under 30 words
   - What the problem asks in simple terms

6. **problem_summary_technical** (MANDATORY): Technical algorithm focus
   - Under 35 words
   - Focus on data structures and algorithms used

7. **time_complexity** (MANDATORY): List of Big O time complexities
   - Standard Big O notation: ["O(n)", "O(log n)", "O(n²)"]

8. **space_complexity** (MANDATORY): List of Big O space complexities
   - Standard Big O notation: ["O(1)", "O(n)", "O(log n)"]

9. **key_insights** (MANDATORY): List of lists with insights
   - Each solution has 2-3 key insights
   - Format: [["insight1", "insight2", "insight3"]]

10. **difficulty_level** (MANDATORY): One of "Easy", "Medium", or "Hard"

**VALIDATION CHECKLIST - VERIFY ALL BEFORE RESPONDING:**
✓ JSON array contains exactly {len(problems_data)} objects
✓ ALL {len(problems_data)} problems are analyzed (no skips)
✓ ALL 10 fields present in EVERY object
✓ problem_summary_simple exists and is under 30 words for ALL problems
✓ problem_summary_technical exists and is under 35 words for ALL problems
✓ category is from the provided list for ALL problems
✓ All arrays use proper list format for ALL problems
✓ JSON array is valid and properly formatted
✓ Exact problem names are used

RESPOND ONLY with the JSON array containing exactly {len(problems_data)} analysis objects. NO explanations, NO markdown blocks, NO additional text."""
    
    return prompt


def read_problem_files(problem_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Read the problem description and solution files.
    
    Args:
        problem_dir: Path to the problem directory
        
    Returns:
        Tuple of (description, solution_code) or (None, None) if files not found
    """
    problem_name = problem_dir.name
    
    # Read problem description
    desc_file = problem_dir / f"{problem_name}_desc.md"
    if not desc_file.exists():
        print(f"⚠️  No description file found for: {problem_name}")
        return None, None
    
    try:
        with open(desc_file, 'r', encoding='utf-8') as f:
            description = f.read()
    except Exception as e:
        print(f"❌ Error reading description for {problem_name}: {str(e)}")
        return None, None
    
    # Read Python solution
    python_folder = problem_dir.parent.parent / "Leet_complete"
    solution_file = python_folder / f"{problem_name}/{problem_name}.py"
    
    if not solution_file.exists():
        print(f"⚠️  No Python solution found for: {problem_name}")
        return description, None
    
    try:
        with open(solution_file, 'r', encoding='utf-8') as f:
            solution_code = f.read()
    except Exception as e:
        print(f"❌ Error reading solution for {problem_name}: {str(e)}")
        return description, None
    
    return description, solution_code


def analyze_with_gemini(prompt: str, max_retries: int = 3) -> Optional[Dict]:
    """
    Send prompt to Gemini and get analysis result.
    
    Args:
        prompt: The analysis prompt
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict containing the analysis or None if failed
    """
    # model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
    model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17')
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting before making the API call
            rate_limiter.wait_if_needed()
            
            print(f"🤖 Calling Gemini AI (attempt {attempt + 1}/{max_retries})...")
            print(f"   {rate_limiter.get_current_rate_info()}")
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for more consistent results
                    max_output_tokens=2000,  # Increased for more detailed prompts
                )
            )
            
            if not response.text:
                print(f"⚠️  Empty response from Gemini (attempt {attempt + 1})")
                continue
            
            # Try to parse JSON from response
            response_text = response.text.strip()
            
            # Remove any markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            analysis_result = json.loads(response_text)
            
            # Validate required fields and attempt to fix missing ones
            required_fields = [
                'data_structures', 'category', 'algorithm_technique',
                'problem_summary_simple', 'problem_summary_technical',
                'time_complexity', 'space_complexity', 'key_insights', 'difficulty_level'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in analysis_result:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  Missing fields in response: {missing_fields}")
                
                # Attempt to provide default values for missing fields
                defaults = {
                    'data_structures': [["unknown"]],
                    'category': "Arrays & Hashing",  # Default category
                    'algorithm_technique': ["analysis not available"],
                    'problem_summary_simple': "Problem analysis incomplete",
                    'problem_summary_technical': "Technical analysis not available",
                    'time_complexity': ["O(n)"],  # Conservative default
                    'space_complexity': ["O(1)"],  # Conservative default
                    'key_insights': [["analysis incomplete"]],
                    'difficulty_level': "Medium"  # Safe middle ground
                }
                
                for field in missing_fields:
                    if field in defaults:
                        analysis_result[field] = defaults[field]
                        print(f"🔧 Applied default value for '{field}'")
                
                # Check if we still have critical missing fields
                still_missing = [f for f in required_fields if f not in analysis_result]
                if still_missing:
                    print(f"❌ Critical fields still missing: {still_missing}")
                    if attempt < max_retries - 1:
                        print(f"🔄 Retrying with simplified prompt focused on missing fields...")
                        # Create a simplified retry prompt focusing on missing fields
                        prompt = create_simplified_retry_prompt(prompt, still_missing)
                        continue
                    else:
                        print(f"❌ Unable to recover missing fields after {max_retries} attempts")
                        return None
                else:
                    print(f"✅ Successfully recovered analysis with default values")
            
            print("✅ Successfully analyzed with Gemini")
            return analysis_result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error (attempt {attempt + 1}): {str(e)}")
            print(f"🔍 Response text preview: {response.text[:300]}...")
            print(f"🔍 Response text end: ...{response.text[-200:]}")
            if "problem_summary_simple" in response.text or "problem_summary_technical" in response.text:
                print("✓ Response contains expected field names")
            else:
                print("❌ Response missing expected field names")
            if attempt < max_retries - 1:
                time.sleep(1)  # Short wait before retry (rate limiter handles main timing)
        
        except Exception as e:
            print(f"❌ Gemini API error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Short wait before retry (rate limiter handles main timing)
    
    print(f"❌ Failed to get valid response from Gemini after {max_retries} attempts")
    return None


def analyze_batch_with_gemini(problems_data: List[Tuple[str, str, str]], max_retries: int = 3) -> Tuple[List[Dict], List[str], float]:
    """
    Send batch prompt to Gemini and get analysis results for multiple problems.
    
    Args:
        problems_data: List of tuples (problem_name, description, solution_code)
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (successful_analyses, failed_problems, processing_time)
    """
    model = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-06-17')
    
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            # Apply rate limiting before making the API call
            rate_limiter.wait_if_needed()
            
            print(f"🤖 Calling Gemini AI for batch of {len(problems_data)} problems (attempt {attempt + 1}/{max_retries})...")
            print(f"   {rate_limiter.get_current_rate_info()}")
            
            # Create batch prompt
            prompt = create_batch_analysis_prompt(problems_data)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for more consistent results
                    max_output_tokens=12000,  # Increased for more detailed batch prompts
                )
            )
            
            if not response.text:
                print(f"⚠️  Empty response from Gemini (attempt {attempt + 1})")
                continue
            
            # Try to parse JSON from response
            response_text = response.text.strip()
            
            # Remove any markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON array
            analysis_results = json.loads(response_text)
            
            if not isinstance(analysis_results, list):
                print(f"⚠️  Expected JSON array but got {type(analysis_results)} (attempt {attempt + 1})")
                continue
            
            # Validate and process results
            successful_analyses = []
            failed_problems = []
            expected_problems = [name for name, _, _ in problems_data]
            
            # Required fields for validation
            required_fields = [
                'problem_name', 'data_structures', 'category', 'algorithm_technique',
                'problem_summary_simple', 'problem_summary_technical',
                'time_complexity', 'space_complexity', 'key_insights', 'difficulty_level'
            ]
            
            # Default values for missing fields
            defaults = {
                'data_structures': [["unknown"]],
                'category': "Arrays & Hashing",
                'algorithm_technique': ["analysis not available"],
                'problem_summary_simple': "Problem analysis incomplete",
                'problem_summary_technical': "Technical analysis not available",
                'time_complexity': ["O(n)"],
                'space_complexity': ["O(1)"],
                'key_insights': [["analysis incomplete"]],
                'difficulty_level': "Medium"
            }
            
            for result in analysis_results:
                if not isinstance(result, dict):
                    continue
                
                problem_name = result.get('problem_name', '')
                
                # Validate problem name matches expected
                if problem_name not in expected_problems:
                    print(f"⚠️  Unexpected problem name: {problem_name}")
                    # Try to find a close match or use first missing problem
                    missing_from_results = [p for p in expected_problems if p not in [r.get('problem_name', '') for r in successful_analyses]]
                    if missing_from_results:
                        original_name = problem_name
                        problem_name = missing_from_results[0]
                        result['problem_name'] = problem_name
                        print(f"🔧 Reassigned result to missing problem: {original_name} -> {problem_name}")
                    else:
                        continue
                
                # Check if all required fields are present and fix missing ones
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    print(f"⚠️  Missing fields for {problem_name}: {missing_fields}")
                    
                    # Apply default values for missing fields
                    for field in missing_fields:
                        if field in defaults:
                            result[field] = defaults[field]
                            print(f"🔧 Applied default value for '{field}' in {problem_name}")
                    
                    # Check if we still have missing fields after applying defaults
                    still_missing = [field for field in required_fields if field not in result]
                    if still_missing:
                        print(f"❌ Critical fields still missing for {problem_name}: {still_missing}")
                        failed_problems.append(problem_name)
                        continue
                    else:
                        print(f"✅ Successfully recovered analysis for {problem_name} with default values")
                
                successful_analyses.append(result)
            
            # Check if we got all expected problems
            processed_names = [r['problem_name'] for r in successful_analyses]
            missing_problems = [name for name in expected_problems if name not in processed_names]
            failed_problems.extend(missing_problems)
            
            processing_time = time.time() - start_time
            
            print(f"✅ Batch analysis completed: {len(successful_analyses)}/{len(problems_data)} successful")
            if failed_problems:
                print(f"⚠️  Failed problems: {failed_problems}")
            
            return successful_analyses, failed_problems, processing_time
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error (attempt {attempt + 1}): {str(e)}")
            print(f"🔍 Batch response text preview: {response.text[:500]}...")
            print(f"🔍 Batch response text end: ...{response.text[-300:]}")
            # Check for expected field names in batch response
            expected_fields = ["problem_summary_simple", "problem_summary_technical", "problem_name"]
            found_fields = [field for field in expected_fields if field in response.text]
            if found_fields:
                print(f"✓ Batch response contains expected field names: {found_fields}")
            else:
                print("❌ Batch response missing expected field names")
            if attempt < max_retries - 1:
                time.sleep(1)  # Short wait before retry (rate limiter handles main timing)
        
        except Exception as e:
            print(f"❌ Gemini API error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Short wait before retry (rate limiter handles main timing)
    
    processing_time = time.time() - start_time
    failed_problems = [name for name, _, _ in problems_data]
    print(f"❌ Failed to get valid batch response from Gemini after {max_retries} attempts")
    return [], failed_problems, processing_time


def save_analysis_result(problem_name: str, analysis: Dict, output_dir: Path):
    """
    Save the analysis result to a JSON file.
    
    Args:
        problem_name: Name of the problem
        analysis: Analysis result dictionary
        output_dir: Directory to save results
    """
    try:
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{problem_name}_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Analysis saved: {output_file}")
        
    except Exception as e:
        print(f"❌ Error saving analysis for {problem_name}: {str(e)}")


def save_batch_performance_metrics(batch_size: int, total_problems: int, successful: int, 
                                  failed: int, processing_time: float, output_dir: Path):
    """
    Save batch processing performance metrics.
    
    Args:
        batch_size: Size of each batch
        total_problems: Total number of problems processed
        successful: Number of successful analyses
        failed: Number of failed analyses
        processing_time: Total processing time
        output_dir: Directory to save metrics
    """
    try:
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = output_dir / f"batch_metrics_{batch_size}_{timestamp}.json"
        
        metrics = {
            "batch_size": batch_size,
            "total_problems": total_problems,
            "successful_analyses": successful,
            "failed_analyses": failed,
            "success_rate": (successful / total_problems * 100) if total_problems > 0 else 0,
            "total_processing_time_seconds": processing_time,
            "average_time_per_problem": (processing_time / total_problems) if total_problems > 0 else 0,
            "timestamp": datetime.now().isoformat(),
            "problems_per_minute": (total_problems / (processing_time / 60)) if processing_time > 0 else 0
        }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Performance metrics saved: {metrics_file}")
        
    except Exception as e:
        print(f"❌ Error saving performance metrics: {str(e)}")


def analyze_problems_in_batches(batch_size: int = 3, specific_problems: Optional[List[str]] = None):
    """
    Analyze problems in batches for performance testing and consolidation.
    
    Args:
        batch_size: Number of problems to analyze in each batch
        specific_problems: Optional list of specific problem names to analyze
    """
    # Get directories
    script_dir = Path(__file__).parent
    leet_complete_dir = script_dir / "Leet_complete"
    output_dir = script_dir / "problem_analysis"
    
    if not leet_complete_dir.exists():
        print(f"❌ Error: Leet_complete directory not found at {leet_complete_dir}")
        return
    
    print(f"🔍 Analyzing problems in batches in: {leet_complete_dir}")
    print(f"📁 Results will be saved to: {output_dir}")
    print(f"📦 Batch size: {batch_size}")
    print("="*80)
    
    # Get problem directories
    if specific_problems:
        problem_dirs = []
        for problem_name in specific_problems:
            problem_dir = leet_complete_dir / problem_name
            if problem_dir.exists():
                problem_dirs.append(problem_dir)
            else:
                print(f"⚠️  Problem directory not found: {problem_name}")
        print(f"📊 Processing {len(problem_dirs)} specific problems")
    else:
        problem_dirs = [d for d in leet_complete_dir.iterdir() if d.is_dir()]
        problem_dirs.sort()
        print(f"📊 Found {len(problem_dirs)} problem directories")
    
    # Filter problems based on user's choice
    unanalyzed_dirs = filter_problems_by_user_choice(problem_dirs, output_dir)
    
    if not unanalyzed_dirs:
        print("✅ All problems already analyzed!")
        return
    
    print(f"📊 {len(unanalyzed_dirs)} problems need analysis")
    
    # Ask user for confirmation
    estimated_batches = (len(unanalyzed_dirs) + batch_size - 1) // batch_size
    print(f"\n💡 This will process {len(unanalyzed_dirs)} problems in ~{estimated_batches} batches of {batch_size}")
    print("⚠️  Make sure you have sufficient API quota.")
    print("🚦 Rate limiting: Automatically limited to 15 requests/minute")
    print(f"🎯 Performance testing: You can compare different batch sizes for efficiency")
    
    confirm = input("\nProceed with batch analysis? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Analysis cancelled by user")
        return
    
    print(f"\n🚀 Starting batch analysis...")
    print("="*80)
    
    # Statistics
    total_problems = len(unanalyzed_dirs)
    total_successful = 0
    total_failed = 0
    all_failed_problems = []
    total_start_time = time.time()
    
    # Process problems in batches
    for batch_num in range(0, len(unanalyzed_dirs), batch_size):
        batch_dirs = unanalyzed_dirs[batch_num:batch_num + batch_size]
        batch_start_idx = batch_num + 1
        batch_end_idx = min(batch_num + batch_size, len(unanalyzed_dirs))
        
        print(f"\n📦 BATCH {(batch_num // batch_size) + 1}/{estimated_batches}")
        print(f"📝 Processing problems {batch_start_idx}-{batch_end_idx} ({len(batch_dirs)} problems)")
        print("-" * 60)
        
        # Prepare batch data
        batch_problems_data = []
        batch_problem_names = []
        
        for problem_dir in batch_dirs:
            problem_name = problem_dir.name
            batch_problem_names.append(problem_name)
            
            description, solution_code = read_problem_files(problem_dir)
            
            if not description or not solution_code:
                print(f"❌ Skipping {problem_name} - missing files")
                all_failed_problems.append(problem_name)
                continue
            
            batch_problems_data.append((problem_name, description, solution_code))
        
        if not batch_problems_data:
            print("❌ No valid problems in this batch")
            continue
        
        print(f"🤖 Analyzing batch: {[name for name, _, _ in batch_problems_data]}")
        
        # Analyze batch
        successful_analyses, failed_problems, processing_time = analyze_batch_with_gemini(batch_problems_data)
        
        # Save successful analyses
        batch_successful = 0
        for analysis in successful_analyses:
            # Add metadata
            analysis['analysis_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            analysis['batch_processed'] = True
            analysis['batch_size'] = len(batch_problems_data)
            
            # Save result
            save_analysis_result(analysis['problem_name'], analysis, output_dir)
            batch_successful += 1
            
            # Show quick summary
            print(f"✅ {analysis['problem_name']}: {analysis.get('category', 'Unknown')} - {analysis.get('algorithm_technique', 'Unknown')}")
        
        # Update statistics
        total_successful += batch_successful
        batch_failed = len(batch_problems_data) - batch_successful
        total_failed += batch_failed
        all_failed_problems.extend(failed_problems)
        
        # Show batch summary
        print(f"\n📊 Batch {(batch_num // batch_size) + 1} Summary:")
        print(f"   ✅ Successful: {batch_successful}/{len(batch_problems_data)}")
        print(f"   ❌ Failed: {batch_failed}")
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        print(f"   🚀 Rate: {len(batch_problems_data)/processing_time:.2f} problems/second")
        
        # Rate limiting between batches is now handled automatically by the rate_limiter
    
    # Final statistics
    total_processing_time = time.time() - total_start_time
    
    print(f"\n{'='*80}")
    print("📊 BATCH ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Batch size: {batch_size}")
    print(f"Total problems: {total_problems}")
    print(f"✅ Successfully analyzed: {total_successful}")
    print(f"❌ Failed to analyze: {total_failed}")
    print(f"🎯 Success rate: {(total_successful/total_problems*100):.1f}%")
    print(f"⏱️  Total processing time: {total_processing_time:.2f}s")
    print(f"🚀 Overall rate: {total_problems/total_processing_time:.2f} problems/second")
    print(f"💰 Estimated cost efficiency: {total_successful} problems / {estimated_batches} API calls = {total_successful/estimated_batches:.2f} problems/call")
    
    if all_failed_problems:
        print(f"\n🔍 FAILED ANALYSES ({len(all_failed_problems)}):")
        for i, problem in enumerate(all_failed_problems, 1):
            print(f"{i:3d}. {problem}")
    
    # Save performance metrics
    save_batch_performance_metrics(
        batch_size, total_problems, total_successful, 
        total_failed, total_processing_time, output_dir
    )
    
    print(f"\n📁 Analysis results saved in: {output_dir}")
    print(f"📊 Performance metrics saved for batch size {batch_size}")
    print("="*80)


def analyze_all_problems():
    """
    Analyze all problems in the Leet_complete directory (single-problem mode).
    """
    # Get directories
    script_dir = Path(__file__).parent
    leet_complete_dir = script_dir / "Leet_complete"
    output_dir = script_dir / "problem_analysis"
    
    if not leet_complete_dir.exists():
        print(f"❌ Error: Leet_complete directory not found at {leet_complete_dir}")
        return
    
    print(f"🔍 Analyzing problems in: {leet_complete_dir}")
    print(f"📁 Results will be saved to: {output_dir}")
    print("="*80)
    
    # Get all problem directories
    problem_dirs = [d for d in leet_complete_dir.iterdir() if d.is_dir()]
    problem_dirs.sort()
    
    if not problem_dirs:
        print("📁 No problem directories found in Leet_complete")
        return
    
    print(f"📊 Found {len(problem_dirs)} problem directories")
    
    # Filter problems based on user's choice
    unanalyzed_dirs = filter_problems_by_user_choice(problem_dirs, output_dir)
    
    if not unanalyzed_dirs:
        print("✅ All problems already analyzed!")
        return
    
    # Ask user for confirmation
    print(f"\n💡 This will use Gemini AI to analyze {len(unanalyzed_dirs)} problems.")
    print("⚠️  Make sure you have sufficient API quota.")
    print("🚦 Rate limiting: Automatically limited to 15 requests/minute")
    
    confirm = input("\nProceed with analysis? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Analysis cancelled by user")
        return
    
    print("\n🚀 Starting analysis...")
    print("="*80)
    
    # Statistics
    total_problems = len(unanalyzed_dirs)
    successful_analyses = 0
    failed_analyses = []
    
    # Process each problem
    for i, problem_dir in enumerate(unanalyzed_dirs, 1):
        problem_name = problem_dir.name
        
        print(f"\n📝 [{i}/{total_problems}] Analyzing: {problem_name}")
        print("-" * 60)
        
        # Check if analysis already exists
        existing_analysis = output_dir / f"{problem_name}_analysis.json"
        if existing_analysis.exists():
            print(f"✅ Analysis already exists for {problem_name} - skipping")
            successful_analyses += 1
            continue
        
        # Read problem files
        description, solution_code = read_problem_files(problem_dir)
        
        if not description or not solution_code:
            print(f"❌ Skipping {problem_name} - missing files")
            failed_analyses.append(problem_name)
            continue
        
        # Create prompt and analyze
        prompt = create_analysis_prompt(description, solution_code)
        analysis_result = analyze_with_gemini(prompt)
        
        if analysis_result:
            # Add metadata
            analysis_result['problem_name'] = problem_name
            analysis_result['analysis_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Save result
            save_analysis_result(problem_name, analysis_result, output_dir)
            successful_analyses += 1
            
            # Show quick summary
            print(f"📊 Category: {analysis_result.get('category', 'Unknown')}")
            print(f"🔧 Technique: {analysis_result.get('algorithm_technique', 'Unknown')}")
            
        else:
            print(f"❌ Failed to analyze {problem_name}")
            failed_analyses.append(problem_name)
        
        # Rate limiting is now handled automatically by the rate_limiter in analyze_with_gemini()
    
    # Print final summary
    print(f"\n{'='*80}")
    print("📊 ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Total problems: {total_problems}")
    print(f"✅ Successfully analyzed: {successful_analyses}")
    print(f"❌ Failed to analyze: {len(failed_analyses)}")
    
    if failed_analyses:
        print(f"\n🔍 FAILED ANALYSES ({len(failed_analyses)}):")
        for i, problem in enumerate(failed_analyses, 1):
            print(f"{i:3d}. {problem}")
    
    print(f"\n📁 Analysis results saved in: {output_dir}")
    print("="*80)


def analyze_specific_problem(problem_name: str):
    """
    Analyze a specific problem.
    
    Args:
        problem_name: Name of the problem to analyze
    """
    script_dir = Path(__file__).parent
    leet_complete_dir = script_dir / "Leet_complete"
    output_dir = script_dir / "problem_analysis"
    problem_dir = leet_complete_dir / problem_name
    
    if not problem_dir.exists():
        print(f"❌ Error: Problem directory not found - {problem_name}")
        return
    
    print(f"🔍 Analyzing specific problem: {problem_name}")
    print("-" * 60)
    
    # Check if problem is in failed problems list
    failed_problems = load_failed_problems()
    if problem_name in failed_problems:
        print(f"🚫 Problem '{problem_name}' is in the failed problems list")
        print("❌ Skipping analysis due to known issues (check failed_problems.json)")
        return
    
    # Check if analysis already exists
    if check_analysis_exists(problem_name, output_dir):
        print(f"⚠️  Analysis already exists for {problem_name}")
        rerun = ask_about_existing_analyses([problem_dir])
        if not rerun:
            print("✅ Skipping analysis (existing result preserved)")
            return
    
    # Read problem files
    description, solution_code = read_problem_files(problem_dir)
    
    if not description or not solution_code:
        print(f"❌ Cannot analyze {problem_name} - missing files")
        return
    
    # Create prompt and analyze
    prompt = create_analysis_prompt(description, solution_code)
    analysis_result = analyze_with_gemini(prompt)
    
    if analysis_result:
        # Add metadata
        analysis_result['problem_name'] = problem_name
        analysis_result['analysis_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display result
        print("\n📊 ANALYSIS RESULT:")
        print("="*60)
        print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
        
        # Save result
        save_analysis_result(problem_name, analysis_result, output_dir)
        print(f"\n✅ Analysis completed and saved for {problem_name}")
    else:
        print(f"❌ Failed to analyze {problem_name}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze LeetCode problems with Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all problems (single mode)
  # - Script will detect existing analyses and ask if you want to skip or rerun them
  python analyze_problems_with_gemini.py

  # Analyze specific problem
  python analyze_problems_with_gemini.py --problem "1-bit-and-2-bit-characters"

  # Batch analysis with default batch size (3)
  python analyze_problems_with_gemini.py --batch

  # Batch analysis with custom batch size
  python analyze_problems_with_gemini.py --batch --batch-size 5

  # Analyze specific problems in batch
  python analyze_problems_with_gemini.py --batch --problems "problem1,problem2,problem3"

  # Performance testing - try different batch sizes
  python analyze_problems_with_gemini.py --batch --batch-size 1
  python analyze_problems_with_gemini.py --batch --batch-size 3  
  python analyze_problems_with_gemini.py --batch --batch-size 5
  python analyze_problems_with_gemini.py --batch --batch-size 10

Features:
  • Smart Analysis Detection: Automatically detects existing analyses
  • Skip/Rerun Choice: Choose to skip existing analyses or rerun them
  • Failed Problems Filter: Automatically skips problems from failed_problems.json
  • Multiple Solutions Support: Handles multiple solution approaches per problem
  • Progress Tracking: Shows which problems are already analyzed
  • Performance Metrics: Track efficiency across different batch sizes
  • Rate Limiting: Built-in 15 requests/minute limit to respect API quotas
  • Intelligent Timing: Automatic request spacing for optimal API usage

Make sure to set GEMINI_API_KEY environment variable first:
  export GEMINI_API_KEY='your-api-key'
        """
    )
    
    parser.add_argument(
        "--problem", 
        type=str, 
        help="Analyze a specific problem by name"
    )
    
    parser.add_argument(
        "--batch", 
        action="store_true", 
        help="Enable batch processing mode for performance testing"
    )
    
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=3, 
        help="Number of problems to process in each batch (default: 3)"
    )
    
    parser.add_argument(
        "--problems", 
        type=str, 
        help="Comma-separated list of specific problems to analyze in batch mode"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.batch_size < 1:
        print("❌ Error: Batch size must be at least 1")
        return
    
    if args.batch_size > 10:
        print("⚠️  Warning: Large batch sizes (>10) may exceed token limits or reduce quality")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            return
    
    # Parse specific problems if provided
    specific_problems = None
    if args.problems:
        specific_problems = [p.strip() for p in args.problems.split(",") if p.strip()]
        if not specific_problems:
            print("❌ Error: No valid problem names provided")
            return
    
    # Execute based on arguments
    if args.problem:
        # Single problem analysis
        print(f"🔍 Single Problem Analysis Mode")
        print("="*50)
        analyze_specific_problem(args.problem)
        
    elif args.batch:
        # Batch analysis mode
        print(f"📦 Batch Analysis Mode")
        print(f"🎯 Performance Testing - Batch Size: {args.batch_size}")
        print("="*50)
        
        if specific_problems:
            print(f"📝 Analyzing specific problems: {specific_problems}")
            if len(specific_problems) < args.batch_size:
                print(f"💡 Note: Batch size ({args.batch_size}) is larger than problem count ({len(specific_problems)})")
                args.batch_size = len(specific_problems)
        
        analyze_problems_in_batches(args.batch_size, specific_problems)
        
    else:
        # Default: single problem mode for all problems
        print(f"🔍 Single Problem Analysis Mode (All Problems)")
        print("="*50)
        analyze_all_problems()


def show_performance_comparison():
    """Show performance comparison across different batch sizes."""
    script_dir = Path(__file__).parent
    output_dir = script_dir / "problem_analysis"
    
    if not output_dir.exists():
        print("📊 No performance metrics found. Run batch analysis first.")
        return
    
    # Find all batch metric files
    metric_files = list(output_dir.glob("batch_metrics_*.json"))
    
    if not metric_files:
        print("📊 No batch performance metrics found.")
        return
    
    print("\n📊 BATCH PERFORMANCE COMPARISON")
    print("="*80)
    print(f"{'Batch Size':<12} {'Success Rate':<12} {'Time/Problem':<15} {'Problems/Min':<15} {'API Efficiency':<15}")
    print("-"*80)
    
    # Load and display metrics
    for metric_file in sorted(metric_files):
        try:
            with open(metric_file, 'r') as f:
                metrics = json.load(f)
            
            batch_size = metrics.get('batch_size', 'Unknown')
            success_rate = f"{metrics.get('success_rate', 0):.1f}%"
            time_per_problem = f"{metrics.get('average_time_per_problem', 0):.2f}s"
            problems_per_min = f"{metrics.get('problems_per_minute', 0):.1f}"
            api_efficiency = f"{metrics.get('successful_analyses', 0)/max(1, (metrics.get('total_problems', 1)//metrics.get('batch_size', 1))):.1f}"
            
            print(f"{batch_size:<12} {success_rate:<12} {time_per_problem:<15} {problems_per_min:<15} {api_efficiency:<15}")
            
        except Exception as e:
            print(f"Error reading {metric_file}: {e}")
    
    print("\n💡 Interpretation:")
    print("- Success Rate: Percentage of problems successfully analyzed")
    print("- Time/Problem: Average processing time per problem")
    print("- Problems/Min: Throughput rate")
    print("- API Efficiency: Average problems processed per API call")
    print("="*80)


if __name__ == "__main__":
    main() 