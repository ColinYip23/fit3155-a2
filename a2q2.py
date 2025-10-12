import sys

# ===============================================================
# Generate Fibonacci numbers up to or slightly above N
# ===============================================================
def generate_fibonacci_up_to(n):
    """
    Generate all Fibonacci numbers up to (and possibly slightly exceeding) n,
    starting from F1 = 1, F2 = 2.

    Args:
        n (int): The upper bound number for Fibonacci generation.

    Returns:
        list[int]: List of Fibonacci numbers [F1, F2, ..., Fk].
    """
    fibs = [1, 2]
    while fibs[-1] <= n:
        fibs.append(fibs[-1] + fibs[-2])
    return fibs


# ===============================================================
# Encode an integer using Fibonacci coding
# ===============================================================
def fibonacci_encode(n):
    """
    Encode a positive integer n into its Fibonacci codeword.

    Steps:
    1. Generate Fibonacci numbers up to n.
    2. Find the largest Fibonacci number <= n.
    3. Subtract and mark that Fibonacci position with '1'.
    4. Repeat until n = 0.
    5. Reverse the bits (since smallest Fibonacci is on the right).
    6. Append an extra '1' at the end for prefix-free termination.

    Args:
        n (int): Positive integer to encode.

    Returns:
        str: Fibonacci codeword (ends with '11').
    """
    if n <= 0:
        raise ValueError("Fibonacci code is only defined for positive integers.")

    fibs = generate_fibonacci_up_to(n)
    code_bits = [0] * (len(fibs) - 1)  # we ignore the last fib > n

    remaining = n
    # Traverse from largest Fibonacci downwards
    for i in range(len(fibs) - 2, -1, -1):
        if fibs[i] <= remaining:
            code_bits[i] = 1
            remaining -= fibs[i]

            # Skip the next Fibonacci number (no consecutive ones allowed)
            # by moving the index one more step down
            # (handled naturally by the loop since we always go down by 1)
    
    # Convert list to string (truncate trailing zeros)
    while code_bits and code_bits[-1] == 0:
        code_bits.pop()
    codeword = ''.join(str(b) for b in code_bits)

    # Append extra 1 for prefix-free property
    return codeword + '1'


# ===============================================================
# Main program logic
# ===============================================================
def main():
    """
    Main function:
    1. Read input filename from command line.
    2. Read positive integers (one per line).
    3. Encode each integer using Fibonacci code.
    4. Write the output codewords to 'output_a2q2.txt'.
    """
    if len(sys.argv) != 2:
        print("Usage: python a2q2.py <input filename>")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = "output_a2q2.txt"

    try:
        with open(input_filename, "r") as infile:
            numbers = [int(line.strip()) for line in infile if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
        sys.exit(1)
    except ValueError:
        print("Error: Input file must contain only positive integers.")
        sys.exit(1)

    # Encode each integer
    results = [fibonacci_encode(n) for n in numbers]

    # Write output to file
    with open(output_filename, "w") as outfile:
        outfile.write("\n".join(results) + "\n")

    print(f"Fibonacci codewords written to {output_filename}.")


if __name__ == "__main__":
    main()
