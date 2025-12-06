from svinst import get_defs
from svinst.defchk import ModInst, PkgInst  # import from the internal module
import sys
import os
from collections import deque


def discover_recursive(start_path):
    """Discover module file names recursively starting from start_path.

    Returns a list of unique filenames (with .sv suffix) that were printed.
    """
    q = deque([start_path])
    visited_files = set()
    printed_names = []
    printed_set = set()

    while q:
        path = q.popleft()
        norm_path = os.path.normpath(path)
        if norm_path in visited_files:
            continue
        visited_files.add(norm_path)

        try:
            defs = get_defs(path)
        except Exception as e:
            print(f"Warning: failed to parse {path}: {e}", file=sys.stderr)
            continue

        if not defs:
            continue

        top = defs[0]
        dirn = os.path.dirname(path) or '.'

        # Top-level module name (one per file)
        top_name = f"{top.name}.sv"
        if top_name not in printed_set:
            printed_set.add(top_name)
            printed_names.append(top_name)
            print(top_name)

        # Generate submodule filenames and enqueue them for processing
        for sub in top.insts:
            if isinstance(sub, (ModInst, PkgInst)):
                sub_filename = f"{sub.name}.sv"
                if sub_filename not in printed_set:
                    printed_set.add(sub_filename)
                    printed_names.append(sub_filename)
                    print(sub_filename)

                # Prefer files in the same directory as the parent
                sub_path = os.path.join(dirn, sub_filename)
                if os.path.exists(sub_path):
                    q.append(sub_path)
                else:
                    # Try the filename relative to cwd if not found in parent dir
                    if os.path.exists(sub_filename):
                        q.append(sub_filename)
                    else:
                        # File not found on disk; skip enqueue but name was still generated
                        print(f"Note: source file for {sub_filename} not found (checked {sub_path})", file=sys.stderr)

    return printed_names


if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else './rtl/jtag.sv'
    filenames = discover_recursive(start)
    # `filenames` contains all unique generated filenames
    out_path = 'modules_list.txt'
    try:
        with open(out_path, 'w') as f:
            for name in filenames:
                f.write(name + '\n')
        print(f"Wrote {len(filenames)} entries to {out_path}")
    except Exception as e:
        print(f"Error writing {out_path}: {e}", file=sys.stderr)
