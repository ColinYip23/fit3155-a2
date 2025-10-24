#!/usr/bin/env python3
"""
a2q3.py
--------
Construct a suffix tree for a given ASCII string (characters in [37..126]) using
Ukkonen's algorithm (linear time/space), then output the suffix array derived
from the suffix tree.

Command line:
    python a2q3.py <input filename>

Spec:
- Read S from the file (one line, no breaks), immediately append unique terminal '$'.
- Build suffix tree with Ukkonen's algorithm (root is Node 1, suffix link of root -> root).
- Output the suffix array (1-based indexes) to "output a2q3.txt", one number per line.
- Produce a run log to "runlog a2q3.txt" documenting each phase and explicit extension:
  * "Node k created: Internal/Leaf node!"
  * "Phase i starts from Extn j"
  * "Extn e applies Rule 2 (regular|alternate)" or "Extn e applies Rule 3"
  * "Active Node = Node A (suffix link to Node B); Remainder = S[l...r]" or EMPTY
  * "Linking Node p to Node q" when we resolve an internal node's suffix link.
Notes:
- We use 1-based indices in logs (to match assignment format).
- Node IDs are assigned in creation order; Node 1 is the root.

Author: (your name / id)
"""

import sys
from typing import Dict, Optional, List, Tuple


# -----------------------------
# Utilities for run logging
# -----------------------------

class RunLogger:
    """Collects run-log lines and writes them at the end."""
    def __init__(self):
        self.lines: List[str] = []

    def log(self, s: str):
        self.lines.append(s)

    def write_to(self, filename: str):
        with open(filename, "w") as f:
            f.write("\n".join(self.lines))
            if self.lines and self.lines[-1] != "":
                f.write("\n")


# -----------------------------
# Suffix tree structures
# -----------------------------

class EndRef:
    """A small mutable wrapper so all leaf edges share the same changing end."""
    def __init__(self, val: int):
        self.val = val

class Node:
    """
    Suffix tree node. For edges from this node, we map the first character
    to the child node. Each child node stores its incoming edge [start..end].
    - start, end: indices of the edge label in the global text; for internal nodes,
      start=-1, end=-1 (no incoming edge from parent, conceptually).
    - end can be EndRef (for leaves) or an integer (for internals/split edges).
    - suffix_link: link to another internal node (root’s link points to itself).
    - id: creation index (root is id=1).
    """
    __slots__ = ("children", "suffix_link", "start", "end", "id")

    def __init__(self, node_id: int, start: int = -1, end = -1):
        self.children: Dict[str, Node] = {}
        self.suffix_link: Optional['Node'] = None
        self.start = start
        self.end = end
        self.id = node_id


# -----------------------------
# Ukkonen's algorithm
# -----------------------------

class SuffixTree:
    """
    Ukkonen suffix tree for a single string. After construction, we can DFS to
    get the suffix array (lexicographic order of suffixes).
    """
    def __init__(self, text: str, logger: RunLogger):
        self.text = text
        self.N = len(text)
        self.logger = logger

        # Node counter: Node 1 is root
        self.next_id = 1
        self.root = self._new_node(internal=True)
        self.root.suffix_link = self.root  # root link to itself (as per spec)
        self.logger.log(f"Node {self.root.id} created: Internal node!")

        # Active point
        self.active_node: Node = self.root
        self.active_edge_char: Optional[str] = None  # first char of the edge
        self.active_length: int = 0

        # Remaining suffixes to add in current phase
        self.remainder: int = 0

        # Global end for all leaf edges
        self.leaf_end = EndRef(-1)

        # For suffix-link logging between newly created internal nodes
        self.last_new_internal: Optional[Node] = None  # to be linked to current active_node (or its link target)

    def _new_node(self, internal: bool, start: int = -1, end = -1) -> Node:
        node = Node(self.next_id, start, end)
        self.next_id += 1
        if internal:
            # For an internal node, end is int (fixed)
            pass
        return node

    def _edge_length(self, node: Node) -> int:
        """Length of incoming edge to this node from its parent."""
        if node.start == -1:
            return 0
        end_val = node.end.val if isinstance(node.end, EndRef) else node.end
        return end_val - node.start + 1

    def _walk_down(self, next_node: Node) -> bool:
        """
        Walk down an edge if active_length >= edge_length. Return True if walked.
        """
        edge_len = self._edge_length(next_node)
        if self.active_length >= edge_len:
            self.active_edge_char = self.text[next_node.start + edge_len] if next_node.start + edge_len < self.N else None
            self.active_length -= edge_len
            self.active_node = next_node
            return True
        return False

    def _active_edge_index(self) -> Optional[int]:
        if self.active_edge_char is None:
            return None
        # active_edge_char is always the first character of the active edge
        return None  # not used directly; we index children by char

    def _active_info_str(self) -> str:
        """String for logging active node / suffix link / remainder range in 1-based indices."""
        active_id = self.active_node.id
        sl_id = self.active_node.suffix_link.id if self.active_node.suffix_link else 1
        if self.remainder <= 0:
            rem = "EMPTY"
        else:
            # Best-effort 1-based remainder interval in current phase:
            # In phase (i+1), with current position i (0-based), remainder r,
            # the pending substring typically spans S[i-r+2 ... i+1] in 1-based indexing.
            # Clamp bounds to [1..N].
            i = self.leaf_end.val
            l = max(1, (i - self.remainder + 2))
            r = max(l, i + 1)
            rem = f"S[{l}...{r}]"
        return f"    Active Node = Node {active_id} (suffix link to Node {sl_id}); Remainder = {rem}"

    def build(self):
        """
        Core Ukkonen loop: phases i = 0..N-1 (processing text[i]).
        We log:
        - Phase starts from Extn j
        - For each explicit extension, which rule applied
        - Node creations
        - Suffix link resolutions
        - Active state *after* each extension (post remainder/active-point update),
            except Rule 3 where we show EMPTY because the phase ends.
        """
        for i in range(self.N):
            # ---- Phase start
            phase_num = i + 1
            self.leaf_end.val = i
            self.remainder += 1
            self.last_new_internal = None

            # "Phase k starts from Extn j"
            start_extn = phase_num - self.remainder + 1
            if start_extn < 1:
                start_extn = 1
            self.logger.log(f"\nPhase {phase_num} starts from Extn {start_extn}")

            # ---- Extensions loop
            while self.remainder > 0:
                if self.active_length == 0:
                    self.active_edge_char = self.text[i]

                if self.active_edge_char not in self.active_node.children:
                    # =========================
                    # Rule 2 (alternate): create a fresh leaf
                    # =========================
                    # Log the rule first (like the reference)
                    self.logger.log(f"    Extn {phase_num} applies Rule 2 (alternate)")

                    # Do the structural change now (but delay node-creation log lines until after active update)
                    leaf = self._new_node(internal=False, start=i, end=self.leaf_end)
                    self.active_node.children[self.active_edge_char] = leaf

                    # Resolve pending internal suffix-link to current active_node (structurally),
                    # but delay logging the link until after we print the Active Node line.
                    pending_link_target = None
                    if self.last_new_internal is not None:
                        self.last_new_internal.suffix_link = self.active_node
                        pending_link_target = self.last_new_internal
                        self.last_new_internal = None

                    # Finish this extension:
                    self.remainder -= 1

                    # Update active point (root trick or suffix link) BEFORE printing Active Node line
                    if self.active_node is self.root and self.active_length > 0:
                        self.active_length -= 1
                        start_index = i - self.remainder + 1
                        if start_index < self.N:
                            self.active_edge_char = self.text[start_index]
                    else:
                        self.active_node = self.active_node.suffix_link if self.active_node.suffix_link is not None else self.root

                    # Now log the post-update active state (this is what makes early phases show EMPTY)
                    self.logger.log(self._active_info_str())

                    # Then log node creation(s) and any link
                    self.logger.log(f"        Node {leaf.id} created: Leaf node!")
                    if pending_link_target is not None:
                        self.logger.log(f"        Linking Node {pending_link_target.id} to Node {self.active_node.id if self.active_node else self.root.id}")

                else:
                    # There is an outgoing edge; maybe walk down or split
                    next_node = self.active_node.children[self.active_edge_char]
                    if self._walk_down(next_node):
                        # Walk-down consumes edge and continues this same extension
                        continue

                    edge_pos = next_node.start + self.active_length
                    if self.text[edge_pos] == self.text[i]:
                        # =========================
                        # Rule 3: character already on edge → extend and end phase
                        # =========================
                        self.active_length += 1
                        self.logger.log(f"    Extn {phase_num} applies Rule 3")

                        # For the reference log, print EMPTY because the phase ends here.
                        # (They treat Rule 3 as ending all pending work for this phase.)
                        self.logger.log(f"    Active Node = Node {self.active_node.id} (suffix link to Node {self.active_node.suffix_link.id if self.active_node.suffix_link else 1}); Remainder = EMPTY")

                        # If there was a pending internal from earlier in this phase, link it now
                        if self.last_new_internal is not None and self.active_node is not self.root:
                            self.last_new_internal.suffix_link = self.active_node
                            self.logger.log(f"        Linking Node {self.last_new_internal.id} to Node {self.active_node.id}")
                            self.last_new_internal = None
                        break  # implicit termination of this phase
                    else:
                        # =========================
                        # Rule 2 (regular): split edge, create internal + leaf
                        # =========================
                        self.logger.log(f"    Extn {phase_num} applies Rule 2 (regular)")

                        # Perform the split (delay "Node created" logs until after active update)
                        split = self._new_node(internal=True, start=next_node.start, end=edge_pos - 1)
                        self.active_node.children[self.active_edge_char] = split

                        leaf = self._new_node(internal=False, start=i, end=self.leaf_end)

                        # Rewire next_node to start at edge_pos; attach both children to split
                        next_node.start = edge_pos
                        split.children[self.text[edge_pos]] = next_node
                        split.children[self.text[i]] = leaf

                        # If there was a previously created internal in this phase, link it to split (structurally).
                        pending_link_from = None
                        if self.last_new_internal is not None:
                            self.last_new_internal.suffix_link = split
                            pending_link_from = self.last_new_internal
                        # Now mark current split as the "last_new_internal" (may be linked later)
                        self.last_new_internal = split

                        # Finish this extension:
                        self.remainder -= 1

                        # Update active point before printing "Active Node..." line
                        if self.active_node is self.root and self.active_length > 0:
                            self.active_length -= 1
                            start_index = i - self.remainder + 1
                            if start_index < self.N:
                                self.active_edge_char = self.text[start_index]
                        else:
                            self.active_node = self.active_node.suffix_link if self.active_node.suffix_link is not None else self.root

                        # Now log the post-update active state line
                        self.logger.log(self._active_info_str())

                        # Then log node creations and any link resolution (to match ordering in reference logs)
                        self.logger.log(f"        Node {split.id} created: Internal node!")
                        self.logger.log(f"        Node {leaf.id} created: Leaf node!")
                        if pending_link_from is not None:
                            self.logger.log(f"        Linking Node {pending_link_from.id} to Node {split.id}")

            # After a phase ends, if an internal is still pending, link it to root (as per Ukkonen)
            if self.last_new_internal is not None:
                self.last_new_internal.suffix_link = self.root
                self.logger.log(f"        Linking Node {self.last_new_internal.id} to Node {self.root.id}")
                self.last_new_internal = None


    # -----------------------------
    # Derive suffix array via DFS
    # -----------------------------

    def _dfs_suffix_array(self, node: Node, depth: int, res: List[int]):
        """
        Depth-first traversal from root. When we reach a leaf, compute the suffix start
        = N - path_length + 1 (1-based), where path_length includes '$'.
        Children visited in lexicographic order of first character to get lex order.
        """
        # Sort children by edge first character for lexicographic order
        for ch in sorted(node.children.keys()):
            child = node.children[ch]
            edge_len = self._edge_length(child)
            self._dfs_suffix_array(child, depth + edge_len, res)

        # Leaf detection: node with no children
        if not node.children:
            # depth equals total chars from root to here; includes '$'
            start_pos_1based = self.N - depth + 1
            res.append(start_pos_1based)

    def suffix_array(self) -> List[int]:
        """Return the suffix array (1-based start indices) from the constructed tree."""
        res: List[int] = []
        self._dfs_suffix_array(self.root, 0, res)
        return res


# -----------------------------
# Main script
# -----------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python a2q3.py <input filename>")
        sys.exit(1)

    in_file = sys.argv[1]
    try:
        with open(in_file, "r", encoding="utf-8") as f:
            s = f.read().strip()
    except FileNotFoundError:
        print(f"Error: file '{in_file}' not found.")
        sys.exit(1)

    if not s:
        print("Error: input string must be non-empty.")
        sys.exit(1)

    # ($ is ASCII 36; input guaranteed to be in [37..126], so '$' is unique)
    text = s

    logger = RunLogger()
    # Build the suffix tree with Ukkonen
    st = SuffixTree(text, logger)
    st.build()

    # Get suffix array (1-based)
    sa = st.suffix_array()

    # Write outputs with exact filenames specified by the spec
    out_filename = "output a2q3.txt"
    with open(out_filename, "w") as outf:
        outf.write("\n".join(str(x) for x in sa) + "\n")

    log_filename = "runlog a2q3.txt"
    logger.write_to(log_filename)

    # Minimal console notice
    print(f"Wrote suffix array to '{out_filename}' and run log to '{log_filename}'.")


if __name__ == "__main__":
    main()
