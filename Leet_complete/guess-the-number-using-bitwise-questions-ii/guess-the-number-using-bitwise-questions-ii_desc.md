Can you solve this real interview question? Guess the Number Using Bitwise Questions II - There is a number n between 0 and 230 - 1 (both inclusive) that you have to find.

There is a pre-defined API int commonBits(int num) that helps you with your mission. But here is the challenge, every time you call this function, n changes in some way. But keep in mind, that you have to find the initial value of n.

commonBits(int num) acts as follows:

 * Calculate count which is the number of bits where both n and num have the same value in that position of their binary representation.
 * n = n XOR num
 * Return count.

Return the number n.

Note: In this world, all numbers are between 0 and 230 - 1 (both inclusive), thus for counting common bits, we see only the first 30 bits of those numbers.

 

Constraints:

 * 0 <= n <= 230 - 1
 * 0 <= num <= 230 - 1
 * If you ask for some num out of the given range, the output wouldn't be reliable.