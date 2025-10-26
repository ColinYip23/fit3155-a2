import sys

# Generate Fibonacci numbers up to or slightly above n
def generate_fibonacci_up_to(n):
    """
    Generate all Fibonacci numbers up to (and possibly slightly exceeding) n,
    starting from F1 = 1, F2 = 2.

    Time Complexity:  O(log n)
        - The number of Fibonacci numbers ≤ n grows logarithmically
          with n because F_k = phi^k / sqrt(5)  ⇒  k = O(log_phi n), meaning there are O(log n) fibonacci numbers up till n.

    Space Complexity: O(log n)
        - We store all Fibonacci numbers up to n in a list of length O(log n).
    """
    fibs = [1, 2]  # O(1)
    while fibs[-1] <= n:  # Iterates O(log n) times
        fibs.append(fibs[-1] + fibs[-2])  # O(1) per iteration
    return fibs  # → Total O(log n) time, O(log n) space



# Encode an integer using Fibonacci encoding
def fibonacci_encode(n):
    """
    Encode a positive integer n into its Fibonacci codeword.

    Steps:
    1. Generate Fibonacci numbers up to n.        O(log n)
    2. Traverse Fibonacci list backward.          O(log n)
    3. Construct bit array and codeword string.   O(log n)

    Overall Time Complexity:  O(log n)
    Overall Space Complexity: O(log n)
    """
    if n <= 0:
        raise ValueError("Fibonacci code is only defined for positive integers.")

    fibs = generate_fibonacci_up_to(n)  # O(log n) time + space
    code_bits = [0] * (len(fibs) - 1)   # O(log n) space

    remaining = n
    # Traverse from largest Fibonacci downwards
    # Loop executes O(log n) times (one per Fibonacci number)
    for i in range(len(fibs) - 2, -1, -1):
        if fibs[i] <= remaining:
            code_bits[i] = 1       # O(1)
            remaining -= fibs[i]   # O(1)
            # Skipping consecutive fib handled implicitly

    # Trim trailing zeros (at most O(log n) operations)
    while code_bits and code_bits[-1] == 0:
        code_bits.pop()

    # Convert list to string (O(log n))
    codeword = ''.join(str(b) for b in code_bits)

    # Append extra 1 for prefix-free property (O(1))
    return codeword + '1'  


# Main program logic
def main():
    """
    Main function:
    1. Read input filename from command line.    O(1)
    2. Read integers from file.                  O(m)
    3. Encode each integer.                      O(m log n)
    4. Write results to output file.             O(m log n)

    where m = number of integers in the file
          n = largest integer among inputs.

    Total Time Complexity:  O(m log n__max), it is n_max since we have to consider the largest number to get the worst case complexities
    Total Space Complexity: O(log n_max)
        - dominated by a single call to fibonacci_encode()
    """
    if len(sys.argv) != 2:
        print("Usage: python a2q2.py <input filename>")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = "output_a2q2.txt"

    # Reading file line by line O(m)
    try:
        with open(input_filename, "r") as infile:
            numbers = [int(line.strip()) for line in infile if line.strip()]  # O(m)
    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
        sys.exit(1)
    except ValueError:
        print("Error: Input file must contain only positive integers.")
        sys.exit(1)

    # Encode each integer O(m log n_max)
    results = [fibonacci_encode(n) for n in numbers]

    # Write output to file O(m log n_max)
    with open(output_filename, "w") as outfile:
        outfile.write("\n".join(results) + "\n")

    print(f"Fibonacci codewords written to {output_filename}.")


if __name__ == "__main__":
    main()
