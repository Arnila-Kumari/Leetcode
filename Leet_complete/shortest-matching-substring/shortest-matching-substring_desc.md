Can you solve this real interview question? Shortest Matching Substring - You are given a string s and a pattern string p, where p contains exactly two '*' characters.

The '*' in p matches any sequence of zero or more characters.

Return the length of the shortest substring in s that matches p. If there is no such substring, return -1.

Note: The empty substring is considered valid.

 

Example 1:

Input: s = "abaacbaecebce", p = "ba*c*ce"

Output: 8

Explanation:

The shortest matching substring of p in s is "baecebce".

Example 2:

Input: s = "baccbaadbc", p = "cc*baa*adb"

Output: -1

Explanation:

There is no matching substring in s.

Example 3:

Input: s = "a", p = "**"

Output: 0

Explanation:

The empty substring is the shortest matching substring.

Example 4:

Input: s = "madlogic", p = "*adlogi*"

Output: 6

Explanation:

The shortest matching substring of p in s is "adlogi".

 

Constraints:

 * 1 <= s.length <= 105
 * 2 <= p.length <= 105
 * s contains only lowercase English letters.
 * p contains only lowercase English letters and exactly two '*'.