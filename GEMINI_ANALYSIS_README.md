# LeetCode Problem Analysis with Gemini AI

This script uses Google's Gemini AI to analyze your LeetCode problems and extract insights about data structures, algorithms, and problem-solving techniques.

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements_gemini.txt
```

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Verify Setup
```bash
python analyze_problems_with_gemini.py --help
```

## 📋 Usage

> **🔍 Smart Analysis Detection**: The script automatically detects existing analyses and asks if you want to skip them (faster) or rerun them (fresh analysis). This prevents unnecessary API calls and gives you control over when to update analyses.

> **🚫 Failed Problems Filter**: The script automatically loads `failed_problems.json` and skips problems with known issues (Wrong Answer, Runtime Error, Time Limit Exceeded). This saves time and API quota by avoiding problematic code.

### Single Problem Mode (Default)

#### Analyze All Problems
```bash
python analyze_problems_with_gemini.py
```

#### Analyze Specific Problem
```bash
python analyze_problems_with_gemini.py --problem "1-bit-and-2-bit-characters"
```

### Batch Processing Mode (New!)

#### Batch Analysis with Default Size (3 problems per batch)
```bash
python analyze_problems_with_gemini.py --batch
```

#### Batch Analysis with Custom Size
```bash
python analyze_problems_with_gemini.py --batch --batch-size 5
```

#### Analyze Specific Problems in Batch
```bash
python analyze_problems_with_gemini.py --batch --problems "problem1,problem2,problem3"
```

### Performance Testing
Test different batch sizes to find optimal performance:
```bash
python analyze_problems_with_gemini.py --batch --batch-size 1
python analyze_problems_with_gemini.py --batch --batch-size 3
python analyze_problems_with_gemini.py --batch --batch-size 5
python analyze_problems_with_gemini.py --batch --batch-size 10
```

## 📊 What You Get

For each problem, the script generates a JSON analysis with support for multiple solution approaches:

```json
{
  "data_structures": [["array", "boolean"]],
  "category": "Arrays & Hashing",
  "algorithm_technique": ["Linear scan with state tracking for bit sequence validation"],
  "problem_summary_simple": "Check if array of 0s and 1s can be decoded ending on 1-bit character",
  "problem_summary_technical": "Validate bit sequence decoding with 1-bit (0) and 2-bit (10,11) characters",
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "key_insights": [
    ["Early termination when reaching end", "Simple state machine for bit parsing"]
  ],
  "difficulty_level": "Easy",
  "problem_name": "1-bit-and-2-bit-characters",
  "analysis_timestamp": "2025-01-12 15:30:45"
}
```

### 🔄 Multiple Solutions Support

When multiple solution approaches are identified, the format expands:

```json
{
  "data_structures": [
    ["array", "boolean"],
    ["array", "hashmap", "counter"]
  ],
  "algorithm_technique": [
    "Linear scan with state tracking",
    "Frequency counting with validation"
  ],
  "key_insights": [
    ["Early termination when reaching end", "Simple state machine"],
    ["Count patterns first", "Validate total matches expected length"]
  ],
  "category": "Arrays & Hashing",
  "problem_summary_simple": "Check if array can be decoded...",
  "problem_summary_technical": "...",
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "difficulty_level": "Easy"
}
```

**Key Changes for Multiple Solutions:**
- `data_structures`: Always a **list of lists** - each inner list represents data structures for one solution approach
- `algorithm_technique`: Always a **list of strings** - each string describes one solution approach
- `key_insights`: Always a **list of lists** - each inner list contains insights for one solution approach

**Even for single solutions**, the format uses lists for consistency:
- Single approach: `"data_structures": [["array", "hashmap"]]` (not `["array", "hashmap"]`)
- Single technique: `"algorithm_technique": ["two pointers"]` (not `"two pointers"`)
- Single insight set: `"key_insights": [["insight1", "insight2"]]` (not `["insight1", "insight2"]`)

## 📁 Output Structure

```
project/
├── problem_analysis/              # Generated analysis results
│   ├── problem1_analysis.json
│   ├── problem2_analysis.json
│   └── ...
├── Leet_complete/                # Your existing problems
├── Python/                      # Your existing solutions
├── failed_problems.json          # Problems to skip (Wrong Answer, Runtime Error, etc.)
└── analyze_problems_with_gemini.py
```

## 🚫 Managing Failed Problems

The script automatically skips problems listed in `failed_problems.json`. This file contains problems categorized by failure type:

```json
{
    "Wrong Answer": ["problem1", "problem2", ...],
    "Runtime Error": ["problem3", "problem4", ...],
    "Time Limit Exceeded": ["problem5", "problem6", ...]
}
```

### Updating Failed Problems List
- **Add problems**: Edit `failed_problems.json` to add new problematic problems
- **Remove problems**: Remove fixed problems from the list to include them in analysis
- **Missing file**: If the file doesn't exist, all problems will be analyzed (script warns about this)

### Example Output with Failed Problems Filtering
```bash
$ python analyze_problems_with_gemini.py

📋 Loaded 133 failed problems from failed_problems.json
🚫 Skipping 15 failed problems:
   ❌ maximal-square
   ❌ longest-turbulent-subarray
   ❌ basic-calculator-iii
   ❌ add-two-numbers
   ❌ sudoku-solver
   ... and 10 more

📊 Found 25 problems with existing analyses:
   ✅ 1-bit-and-2-bit-characters
   ✅ 3sum
   ... and 23 more

❓ What would you like to do with these 25 already-analyzed problems?
   1. Skip them (faster, use existing results)
   2. Rerun analysis (will overwrite existing results)
```

## 🔍 Features

### Single Problem Mode
- **Smart Retry Logic**: Handles API failures with exponential backoff
- **Rate Limiting**: 2-second delays between requests to respect API limits
- **Smart Analysis Detection**: Automatically detects existing analyses and gives you choice to skip or rerun them
- **Failed Problems Filter**: Automatically skips problems listed in `failed_problems.json` to avoid known issues
- **Resume Capability**: Interactive choice to skip already analyzed problems or rerun them
- **Comprehensive Analysis**: 9 different insights per problem
- **Error Handling**: Graceful handling of missing files or API issues
- **Progress Tracking**: Real-time progress updates with existing analysis counts

### Batch Processing Mode (NEW!)
- **Consolidation**: Analyze multiple problems in a single API call
- **Performance Testing**: Compare different batch sizes for optimal efficiency
- **Cost Efficiency**: Reduce API calls while maintaining quality
- **Metrics Tracking**: Detailed performance metrics saved for each batch size
- **Quality Monitoring**: Track when batch size affects analysis quality
- **Flexible Batching**: Custom batch sizes and specific problem selection

## 🎯 Problem Categories

The script categorizes problems into:
- Arrays & Hashing
- Two Pointers
- Binary Search
- Stack
- Sliding Window
- Linked List
- Trees
- Tries
- Heap / Priority Queue
- Backtracking
- Graphs
- 1-D Dynamic Programming
- Intervals
- Advanced Graphs
- Math & Geometry
- 2-D Dynamic Programming
- Bit Manipulation
- Greedy

## ⚠️ Important Notes

1. **API Costs**: Each analysis uses Gemini API credits. Monitor your usage.
2. **Rate Limits**: Script includes delays to avoid hitting rate limits.
3. **File Requirements**: Needs both `_desc.md` and corresponding `.py` files.
4. **JSON Output**: All results are in valid JSON format for easy processing.

## 🔧 Troubleshooting

### API Key Issues
```bash
# Check if environment variable is set
echo $GEMINI_API_KEY

# Set it temporarily for current session
export GEMINI_API_KEY="your-key"
```

### Missing Files
The script will warn about missing description or solution files and skip them.

### JSON Parsing Errors
If Gemini returns invalid JSON, the script retries up to 3 times with different approaches.

## 📈 Batch Processing & Performance Testing

### Benefits of Batch Processing
- **Cost Efficiency**: Process 3-10 problems per API call vs. 1 problem per call
- **Speed**: Significantly faster for large datasets
- **Reduced Rate Limiting**: Fewer API calls means less chance of hitting limits
- **Performance Insights**: Compare different batch sizes to find optimal configuration

### Performance Metrics
Each batch run generates detailed metrics:
```json
{
  "batch_size": 5,
  "total_problems": 50,
  "successful_analyses": 48,
  "success_rate": 96.0,
  "total_processing_time_seconds": 120.5,
  "average_time_per_problem": 2.41,
  "problems_per_minute": 24.9,
  "timestamp": "2025-01-12T15:30:45"
}
```

### Finding Optimal Batch Size
Test different sizes to find the sweet spot:

| Batch Size | Success Rate | Speed | API Efficiency | Notes |
|------------|-------------|-------|----------------|-------|
| 1 | 100% | Slow | 1 problem/call | Most reliable |
| 3 | 95-98% | Fast | 3 problems/call | Good balance |
| 5 | 90-95% | Faster | 5 problems/call | Efficient |
| 10+ | 80-90% | Fastest | 10+ problems/call | May reduce quality |

### When Quality Degrades
Monitor these indicators:
- Success rate drops below 90%
- Missing required fields in responses
- Inconsistent categorization
- Truncated or incomplete analyses

### Best Practices
1. Start with batch size 3-5 for testing
2. Monitor success rates and adjust accordingly
3. Use single-problem mode for critical analyses
4. Check performance metrics to optimize workflow

## 🎉 Example Output

```
🔍 Analyzing problems in: /path/to/Leet_complete
📁 Results will be saved to: /path/to/problem_analysis
================================================================================
📊 Found 150 problem directories

💡 This will use Gemini AI to analyze 150 problems.
⚠️  Make sure you have sufficient API quota.

Proceed with analysis? (y/n): y

🚀 Starting analysis...
================================================================================

📝 [1/150] Analyzing: 1-bit-and-2-bit-characters
------------------------------------------------------------
🤖 Calling Gemini AI (attempt 1/3)...
✅ Successfully analyzed with Gemini
📁 Analysis saved: problem_analysis/1-bit-and-2-bit-characters_analysis.json
📊 Category: Arrays & Hashing
🔧 Technique: Linear scan with state tracking for bit sequence validation
⏳ Waiting 2 seconds before next analysis...
``` 