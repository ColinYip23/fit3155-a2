#!/usr/bin/env python3
"""
a2q4.py
--------
Compressed encoding of a suffix tree.

This program encodes both:
  (I)  The Burrows-Wheeler Transform (BWT) of the input string
  (II) The suffix tree structure

using Fibonacci integer coding (from a2q2.py), suffix tree (from a2q3.py) and Huffman coding.

Command line:
    python a2q4.py <input filename>

Output:
    output_a2q4_bin  — binary encoding of the bwt of the input string and suffix tree
"""

import sys
import heapq
from typing import List, Tuple, Dict, Optional

from a2q2 import fibonacci_encode
from a2q3 import SuffixTree, EndRef, Node as STNode


# PART I — BWT + Huffman + RLE
def bwt_from_sa(s: str, sa: List[int]) -> str:
    """Compute the Burrows-Wheeler Transform given S and its 1-based suffix array."""
    n = len(s)
    return ''.join(s[-1] if i == 1 else s[i - 2] for i in sa)


class DummyLogger:
    def log(self, *args, **kwargs):
        pass


def build_huffman_codes(text: str) -> Dict[str, str]:
    """
    Build deterministic Huffman codes 
    - Lower frequency = left (0), higher = right (1)
    - Ties then lexicographically smaller symbol first
    """
    freq: Dict[str, int] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1

    # Single character case
    if len(freq) == 1:
        only = next(iter(freq))
        return {only: "1"}

    class Node:
        def __init__(self, freq, sym=None, left=None, right=None):
            self.freq, self.sym, self.left, self.right = freq, sym, left, right

        def __lt__(self, other):
            if self.freq != other.freq:
                return self.freq < other.freq
            if self.sym is not None and other.sym is not None:
                return self.sym < other.sym
            if self.sym is not None:
                return True
            if other.sym is not None:
                return False
            return False

    heap: List[Node] = [Node(f, c) for c, f in sorted(freq.items())]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        heapq.heappush(heap, Node(left.freq + right.freq, None, left, right))

    root = heap[0]
    codes: Dict[str, str] = {}

    def traverse(node, prefix):
        if node.sym is not None:
            codes[node.sym] = prefix or "1"
            return
        traverse(node.left, prefix + "0")
        traverse(node.right, prefix + "1")

    traverse(root, "")
    return codes


def rle_runs(s: str) -> List[Tuple[int, str]]:
    """Run-length encode string into [(count, char), …]."""
    if not s:
        return []
    runs, count = [], 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            runs.append((count, s[i - 1]))
            count = 1
    runs.append((count, s[-1]))
    return runs


def encode_part_I_bwt(s: str, sa: List[int]) -> str:
    """Encode the BWT section (Part I)."""
    bwt = bwt_from_sa(s, sa)
    bits: List[str] = []

    bits.append(fibonacci_encode(len(bwt)))              # (a) length
    distinct = sorted(set(bwt))
    bits.append(fibonacci_encode(len(distinct)))         # (b) #distinct

    codes = build_huffman_codes(bwt)
    for ch in distinct:                                  # (c) 7 bit ascii + code
        ascii7 = format(ord(ch), "07b")
        code = codes[ch]
        bits.append(ascii7)
        bits.append(fibonacci_encode(len(code)))
        bits.append(code)

    for run_len, ch in rle_runs(bwt):                    # (d) RLE BWT
        bits.append(fibonacci_encode(run_len))
        bits.append(codes[ch])

    return "".join(bits)


# PART II — Encode suffix tree directly from a2q3
def encode_part_II_from_q3_tree(s: str, st: SuffixTree) -> str:
    """
    Encode the suffix tree directly (using the structure from a2q3).
    Traverses recursively in lexicographic order of edge labels.
    """
    bits: List[str] = []

    def edge_label_range(node: STNode) -> Optional[Tuple[int, int]]:
        """Return (start,end) of the incoming edge (1-based inclusive)."""
        if node.start == -1:
            return None
        end_val = node.end.val if isinstance(node.end, EndRef) else node.end
        return (node.start + 1, end_val + 1)

    def sorted_children(node: STNode):
        return sorted(node.children.items())

    def dfs(node: STNode, depth=0):
        prefix = "  " * depth
        for ch, child in sorted_children(node):
            rng = edge_label_range(child)
            if rng is None:
                continue
            start, end = rng

            # DOWN
            bits.append("0")
            bits.append(fibonacci_encode(start))
            bits.append(fibonacci_encode(end))


            if not child.children:
                # LEAF UP
                path_len = end - (child.start + 1) + 1
                suffix_index = st.N - (depth + path_len) + 1

                bits.append("1")
                bits.append(fibonacci_encode(suffix_index))

            else:
                # INTERNAL subtree
                dfs(child, depth + (end - start + 1))

                bits.append("1")


    dfs(st.root)

    bits.append("1")


    return "".join(bits)


# Bit-packing utility
def write_bits_to_bin(bitstring: str, filename: str) -> None:
    """Write a bitstring to a binary file, padding to byte boundary."""
    pad = (8 - len(bitstring) % 8) % 8
    bitstring += "0" * pad
    data = bytearray(int(bitstring[i:i + 8], 2) for i in range(0, len(bitstring), 8))
    with open(filename, "wb") as f:
        f.write(data)


def main():
    if len(sys.argv) != 2:
        print("Usage: python a2q4.py <input filename>")
        sys.exit(1)

    infile = sys.argv[1]
    with open(infile, "r", encoding="utf-8") as f:
        S = f.read().strip()

    # Ensure unique terminal
    if not S.endswith("$"):
        S += "$"

    # Build suffix tree
    st = SuffixTree(S, logger=DummyLogger())
    st.build()
    sa = st.suffix_array()  # use suffix array from the same tree

    # encode Part I (BWT)
    part1_bits = encode_part_I_bwt(S, sa)

    # encode Part II (suffix tree structure)
    part2_bits = encode_part_II_from_q3_tree(S, st)

    # concatenate both parts
    full_bits = part1_bits + part2_bits


    with open("output_a2q4_bits.txt", "w", encoding="utf-8") as f:
        f.write(full_bits + "\n")
        f.write(f"(Total bits: {len(full_bits)})\n")

    write_bits_to_bin(full_bits, "output_a2q4.bin")
    print("Binary encoding written to output_a2q4.bin")


if __name__ == "__main__":
    main()
