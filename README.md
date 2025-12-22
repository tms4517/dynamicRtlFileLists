from svinst import get_defs
from svinst.defchk import ModInst, PkgInst  # import from the internal module
import sys
import os
import argparse
from collections import deque


def _get_defs_safe(path, includes):
    """Call svinst.get_defs with includes and handle exceptions.

    Returns the defs list or None on failure.
    """
    try:
        return get_defs(path, includes=includes or [])
    except Exception as e:
        print(f"Warning: failed to parse {path}: {e}", file=sys.stderr)
        return None


def _find_in_includes(sub_filename, includes):
    """Search include directories recursively for sub_filename.

    Returns the first matching absolute path or None.
    """
    for inc in includes or []:
        for root, _, files in os.walk(inc):
            if sub_filename in files:
                return os.path.join(root, sub_filename)
    return None


def _resolve_submodule_abs(dirn, sub_filename, includes):
    """Resolve a submodule path when absolute paths are requested.

    Returns a tuple (chosen_abs, enqueue_path) where enqueue_path is a
    filesystem path to append to the work queue (or None if nothing to enqueue).
    """
    candidate_in_parent = os.path.join(dirn, sub_filename)
    if os.path.exists(candidate_in_parent):
        return os.path.abspath(candidate_in_parent), candidate_in_parent

    found = _find_in_includes(sub_filename, includes)
    if found:
        return os.path.abspath(found), found

    if os.path.exists(sub_filename):
        return os.path.abspath(sub_filename), sub_filename

    # Not found on disk; return the absolute path where it would be
    chosen_abs = os.path.abspath(os.path.join(dirn, sub_filename))
    return chosen_abs, None


def _resolve_submodule_rel(dirn, sub_filename, includes):
    """Resolve a submodule path when relative (non-absolute) output is requested.

    Returns a tuple (chosen_abs, enqueue_path) similar to `_resolve_submodule_abs`.
    """
    sub_path = os.path.join(dirn, sub_filename)
    if os.path.exists(sub_path):
        return os.path.abspath(sub_path), sub_path

    found = _find_in_includes(sub_filename, includes)
    if found:
        return os.path.abspath(found), found

    if os.path.exists(sub_filename):
        return os.path.abspath(sub_filename), sub_filename

    # Not found; compute canonical location
    chosen_abs = os.path.abspath(os.path.join(dirn, sub_filename))
    return chosen_abs, None


def _display_name_for(abs_path, root_dir, absolute_path):
    """Return the string to print for abs_path depending on absolute_path flag."""
    return abs_path if absolute_path else os.path.relpath(abs_path, root_dir)


def discover_recursive(start_path, absolute_path=False, includes=None, include_incdirs=False):
    """Discover module file names recursively starting from start_path.

    Returns a tuple (printed_names, top_module_name) where printed_names is a list
    of unique filenames (or absolute file paths when `absolute_path` is True)
    that were printed and top_module_name is the name of the top-level module
    (or None if not found).
    If include_incdirs is True, +incdir+<dir> lines are inserted before files from new directories.
    """
    if start_path.endswith('.v'):
        submodule_ext = '.v'
    else:
        submodule_ext = '.sv'
    q = deque([start_path])
    visited_files = set()
    printed_names = []
    printed_paths_set = set()
    incdir_set = set()

    start_abs = os.path.abspath(start_path)
    root_dir = os.path.dirname(start_abs) or os.path.abspath('.')
    top_module = None

    def emit_incdir_for(abs_path):
        dir_path = os.path.dirname(abs_path)
        if dir_path not in incdir_set:
            incdir_set.add(dir_path)
            # Use relative or absolute path for incdir, matching file output
            incdir_str = dir_path if absolute_path else os.path.relpath(dir_path, root_dir)
            # Always add trailing slash for incdir
            if not incdir_str.endswith('/'):
                incdir_str += '/'
            incdir_line = f'+incdir+{incdir_str}'
            printed_names.append(incdir_line)
            print(incdir_line)

    while q:
        path = q.popleft()
        norm_path = os.path.normpath(path)
        if norm_path in visited_files:
            continue
        visited_files.add(norm_path)

        defs = _get_defs_safe(path, includes)
        if not defs:
            continue

        top = defs[0]
        if top_module is None:
            top_module = top.name
        dirn = os.path.dirname(path) or '.'

        abs_path = os.path.abspath(path)
        if abs_path not in printed_paths_set:
            printed_paths_set.add(abs_path)
            if include_incdirs:
                emit_incdir_for(abs_path)
            display_name = _display_name_for(abs_path, root_dir, absolute_path)
            printed_names.append(display_name)
            print(display_name)

        for sub in top.insts:
            if not isinstance(sub, (ModInst, PkgInst)):
                continue

            sub_filename = f"{sub.name}{submodule_ext}"

            if absolute_path:
                chosen_abs, enqueue_path = _resolve_submodule_abs(dirn, sub_filename, includes)
            else:
                chosen_abs, enqueue_path = _resolve_submodule_rel(dirn, sub_filename, includes)

            if enqueue_path:
                q.append(enqueue_path)

            if chosen_abs not in printed_paths_set:
                printed_paths_set.add(chosen_abs)
                if include_incdirs:
                    emit_incdir_for(chosen_abs)
                if enqueue_path is None and not os.path.exists(chosen_abs):
                    checked_path = os.path.join(dirn, sub_filename)
                    err_msg = f"ERROR: source file for {sub_filename} not found (checked {checked_path})"
                    printed_names.append(err_msg)
                    print(err_msg)
                else:
                    display_name = _display_name_for(chosen_abs, root_dir, absolute_path)
                    printed_names.append(display_name)
                    print(display_name)

    return printed_names, top_module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Discover SystemVerilog module files and emit a .f list')
    parser.add_argument('start', help='input file path (top-level .sv)')
    parser.add_argument('--absolute_path', action='store_true', help='Output absolute file paths in the generated .f')
    parser.add_argument('-I', '--include', action='append', default=[], dest='includes',
                        help='Add an include directory to pass to svinst.get_defs (may be given multiple times)')
    parser.add_argument('--include_incdirs', action='store_true', help='Emit +incdir+<dir> for each directory encountered')
    args = parser.parse_args()

    # Expand each include path to include all subdirectories
    expanded_includes = []
    for inc in args.includes:
        for root, dirs, files in os.walk(inc):
            expanded_includes.append(root)

    start = args.start
    filenames, top = discover_recursive(start, absolute_path=args.absolute_path, includes=expanded_includes, include_incdirs=args.include_incdirs)
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
