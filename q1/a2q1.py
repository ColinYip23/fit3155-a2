import random
import sys


# Modular exponentiation using repeated squaring
def mod_exp(base, exponent, modulus):
    """
    Compute (base^exponent) % modulus efficiently using repeated squaring.
    This avoids overflow and runs in O(log exponent) time.

    Args:
        base (int): The base number.
        exponent (int): The exponent.
        modulus (int): The modulus.

    Returns:
        int: (base^exponent) % modulus.
    """
    result = 1
    base = base % modulus  # handle large bases

    while exponent > 0:
        # If exponent is odd, multiply result with current base
        if exponent % 2 == 1:
            result = (result * base) % modulus
        # Square the base
        base = (base * base) % modulus
        exponent //= 2
    return result


# Miller-Rabin primality test
def is_probable_prime(n, k=20):
    """
    Miller-Rabin probabilistic primality test.
    Repeats k times for higher confidence.

    Args:
        n (int): Number to test.
        k (int): Number of testing rounds (default = 20).

    Returns:
        bool: True if n is probably prime, False if composite.
    """
    # Handle small numbers and even numbers quickly
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    # Express n-1 as 2^r * d with d odd
    r = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        r += 1

    # Perform k rounds of testing
    for _ in range(k):
        a = random.randrange(2, n - 2)  # random base a in between 2 and n−2
        x = mod_exp(a, d, n)  # compute a^d mod n using repeated squaring

        if x == 1 or x == n - 1:
            continue  # possible prime so far

        # Repeatedly square x and check if it becomes n-1
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            # Composite found
            return False
    return True  # Probably prime


# Generate a random d-digit prime number
def generate_d_digit_prime(d):
    """
    Generate a random prime number with exactly d digits.

    Args:
        d (int): Number of digits (100 ≤ d ≤ 1000).

    Returns:
        int: A d-digit prime number.
    """
    assert 100 <= d <= 1000, "d must be between 100 and 1000"

    # Define lower and upper bounds for d-digit numbers
    lower = 10 ** (d - 1)
    upper = 10 ** d - 1

    while True:
        # Generate a random odd d-digit number
        candidate = random.randrange(lower, upper)
        candidate |= 1  # make it odd

        # Check primality using Miller-Rabin
        if is_probable_prime(candidate):
            return candidate


# Main execution
def main():
    """
    Main function:
    1. Parse command-line argument.
    2. Generate random d-digit prime.
    3. Write result to output_a2q1.txt.
    """
    if len(sys.argv) != 2:
        print("Usage: python a2q1.py <d>")
        sys.exit(1)

    try:
        d = int(sys.argv[1])
        if not (100 <= d <= 1000):
            raise ValueError
    except ValueError:
        print("Error: d must be an integer between 100 and 1000.")
        sys.exit(1)

    prime_number = generate_d_digit_prime(d)

    # Write to output file
    with open("output_a2q1.txt", "w") as f:
        f.write(str(prime_number) + "\n")

    print(f"A {d}-digit prime number has been written to output_a2q1.txt.")


if __name__ == "__main__":
    main()
