Can you solve this real interview question? Beautiful Pairs - You are given two 0-indexed integer arrays nums1 and nums2 of the same length. A pair of indices (i,j) is called beautiful if|nums1[i] - nums1[j]| + |nums2[i] - nums2[j]| is the smallest amongst all possible indices pairs where i < j.

Return the beautiful pair. In the case that there are multiple beautiful pairs, return the lexicographically smallest pair.

Note that

 * |x| denotes the absolute value of x.
 * A pair of indices (i1, j1) is lexicographically smaller than (i2, j2) if i1 < i2 or i1 == i2 and j1 < j2.

 

Example 1:


Input: nums1 = [1,2,3,2,4], nums2 = [2,3,1,2,3]
Output: [0,3]
Explanation: Consider index 0 and index 3. The value of |nums1[i]-nums1[j]| + |nums2[i]-nums2[j]| is 1, which is the smallest value we can achieve.


Example 2:


Input: nums1 = [1,2,4,3,2,5], nums2 = [1,4,2,3,5,1]
Output: [1,4]
Explanation: Consider index 1 and index 4. The value of |nums1[i]-nums1[j]| + |nums2[i]-nums2[j]| is 1, which is the smallest value we can achieve.


 

Constraints:

 * 2 <= nums1.length, nums2.length <= 105
 * nums1.length == nums2.length
 * 0 <= nums1i <= nums1.length
 * 0 <= nums2i <= nums2.length