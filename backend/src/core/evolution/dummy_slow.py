
import time

def slow_sum(n):
    """
    Calculates the sum of numbers from 0 to n-1 using a nested loop.
    This is intentionally O(n^2) for demonstration purposes.
    """
    total = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                total += i
    return total
