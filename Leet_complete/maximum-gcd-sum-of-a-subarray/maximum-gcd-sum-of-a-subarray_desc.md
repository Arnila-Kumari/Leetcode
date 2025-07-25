Can you solve this real interview question? Maximum GCD-Sum of a Subarray - You are given an array of integers nums and an integer k.

The gcd-sum of an array a is calculated as follows:

 * Let s be the sum of all the elements of a.
 * Let g be the greatest common divisor of all the elements of a.
 * The gcd-sum of a is equal to s * g.

Return the maximum gcd-sum of a subarray of nums with at least k elements.

 

Example 1:


Input: nums = [2,1,4,4,4,2], k = 2
Output: 48
Explanation: We take the subarray [4,4,4], the gcd-sum of this array is 4 * (4 + 4 + 4) = 48.
It can be shown that we can not select any other subarray with a gcd-sum greater than 48.

Example 2:


Input: nums = [7,3,9,4], k = 1
Output: 81
Explanation: We take the subarray [9], the gcd-sum of this array is 9 * 9 = 81.
It can be shown that we can not select any other subarray with a gcd-sum greater than 81.

 

Constraints:

 * n == nums.length
 * 1 <= n <= 105
 * 1 <= nums[i] <= 106
 * 1 <= k <= n