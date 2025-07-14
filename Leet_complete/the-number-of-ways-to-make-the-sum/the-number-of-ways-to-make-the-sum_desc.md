Can you solve this real interview question? The Number of Ways to Make the Sum - You have an infinite number of coins with values 1, 2, and 6, and only 2 coins with value 4.

Given an integer n, return the number of ways to make the sum of n with the coins you have.

Since the answer may be very large, return it modulo 109 + 7.

Note that the order of the coins doesn't matter and [2, 2, 3] is the same as [2, 3, 2].

 

Example 1:

Input: n = 4

Output: 4

Explanation:

Here are the four combinations: [1, 1, 1, 1], [1, 1, 2], [2, 2], [4].

Example 2:

Input: n = 12

Output: 22

Explanation:

Note that [4, 4, 4] is not a valid combination since we cannot use 4 three times.

Example 3:

Input: n = 5

Output: 4

Explanation:

Here are the four combinations: [1, 1, 1, 1, 1], [1, 1, 1, 2], [1, 2, 2], [1, 4].

 

Constraints:

 * 1 <= n <= 105