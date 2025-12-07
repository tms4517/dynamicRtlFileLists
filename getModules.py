from svinst import get_defs
from svinst.defchk import ModInst, PkgInst  # import from the internal module
import sys
import os
import argparse
from collections import deque


def discover_recursive(start_path, absolute_path=False, includes=None):
    """Discover module file names recursively starting from start_path.

    Returns a tuple (printed_names, top_module_name) where printed_names is a list
    of unique filenames (or absolute file paths when `absolute_path` is True)
    that were printed and top_module_name is the name of the top-level module
    (or None if not found).
    """
    q = deque([start_path])
    visited_files = set()
    printed_names = []
    printed_paths_set = set()
    # canonical root dir (absolute) used for computing relative printed paths
    start_abs = os.path.abspath(start_path)
    root_dir = os.path.dirname(start_abs) or os.path.abspath('.')
    top_module = None

    while q:
        path = q.popleft()
        norm_path = os.path.normpath(path)
        if norm_path in visited_files:
            continue
        visited_files.add(norm_path)

        try:
            # pass include directories through to get_defs when provided
            defs = get_defs(path, includes=includes or [])
        except Exception as e:
            print(f"Warning: failed to parse {path}: {e}", file=sys.stderr)
            continue

        if not defs:
            continue

        top = defs[0]
        if top_module is None:
            top_module = top.name
        dirn = os.path.dirname(path) or '.'

        # Top-level entry: present the file either as absolute path or
        # relative to the top-level module directory
        abs_path = os.path.abspath(path)
        if abs_path not in printed_paths_set:
            printed_paths_set.add(abs_path)
            display_name = abs_path if absolute_path else os.path.relpath(abs_path, root_dir)
            printed_names.append(display_name)
            print(display_name)

        # Generate submodule filenames and enqueue them for processing
        for sub in top.insts:
            if isinstance(sub, (ModInst, PkgInst)):
                sub_filename = f"{sub.name}.sv"

                if absolute_path:
                    # Prefer files in the same directory as the parent
                    candidate_in_parent = os.path.join(dirn, sub_filename)
                    if os.path.exists(candidate_in_parent):
                        chosen_abs = os.path.abspath(candidate_in_parent)
                        q.append(candidate_in_parent)
                    else:
                        # If not in parent, search includes recursively for the file
                        found = None
                        for inc in includes or []:
                            for root, _, files in os.walk(inc):
                                if sub_filename in files:
                                    found = os.path.join(root, sub_filename)
                                    break
                            if found:
                                break

                        if found:
                            chosen_abs = os.path.abspath(found)
                            q.append(found)
                        elif os.path.exists(sub_filename):
                            chosen_abs = os.path.abspath(sub_filename)
                            q.append(sub_filename)
                        else:
                            # File not found; still produce the absolute path where it would be
                            chosen_abs = os.path.abspath(os.path.join(dirn, sub_filename))
                            print(f"Note: source file for {sub_filename} not found (checked {candidate_in_parent})", file=sys.stderr)

                    if chosen_abs not in printed_paths_set:
                        printed_paths_set.add(chosen_abs)
                        printed_names.append(chosen_abs)
                        print(chosen_abs)
                else:
                    # Prefer files in the same directory as the parent
                    sub_path = os.path.join(dirn, sub_filename)
                    # Determine chosen absolute path for printing/enqueueing
                    if os.path.exists(sub_path):
                        chosen_abs = os.path.abspath(sub_path)
                        q.append(sub_path)
                    else:
                        # Search include directories recursively for the file
                        found = None
                        for inc in includes or []:
                            for root, _, files in os.walk(inc):
                                if sub_filename in files:
                                    found = os.path.join(root, sub_filename)
                                    break
                            if found:
                                break

                        if found:
                            chosen_abs = os.path.abspath(found)
                            q.append(found)
                        else:
                            # Try the filename relative to cwd if not found in parent dir or includes
                            if os.path.exists(sub_filename):
                                chosen_abs = os.path.abspath(sub_filename)
                                q.append(sub_filename)
                            else:
                                # File not found on disk; still compute the path where it would be
                                chosen_abs = os.path.abspath(os.path.join(dirn, sub_filename))
                                print(f"Note: source file for {sub_filename} not found (checked {sub_path})", file=sys.stderr)

                    # Display as relative path to the top-level module directory
                    display_name = os.path.relpath(chosen_abs, root_dir)
                    if chosen_abs not in printed_paths_set:
                        printed_paths_set.add(chosen_abs)
                        printed_names.append(display_name)
                        print(display_name)

    return printed_names, top_module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Discover SystemVerilog module files and emit a .f list')
    parser.add_argument('start', help='input file path (top-level .sv)')
    parser.add_argument('--absolute_path', action='store_true', help='Output absolute file paths in the generated .f')
    parser.add_argument('-I', '--include', action='append', default=[], dest='includes',
                        help='Add an include directory to pass to svinst.get_defs (may be given multiple times)')
    args = parser.parse_args()

    start = args.start
    filenames, top = discover_recursive(start, absolute_path=args.absolute_path, includes=args.includes)
    if not top:
        print(f"Error: could not determine top-level module name from {start}", file=sys.stderr)
        sys.exit(1)
    out_path = f"{top}.f"
    try:
        with open(out_path, 'w') as f:
            for name in filenames:
                f.write(name + '\n')
        print(f"Wrote {len(filenames)} entries to {out_path}")
    except Exception as e:
        print(f"Error writing {out_path}: {e}", file=sys.stderr)
        sys.exit(1)
