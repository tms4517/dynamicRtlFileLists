# Dynamic RTL File Lists

Dynamically generate file-list (`.f`) files for SystemVerilog projects.

**Purpose:**
- Discover module/package source files from a top-level SystemVerilog file.
- Generate an ordered `.f` file for simulators or tools that accept Verilog filelists.

**Features:**
- Recursively finds instantiated modules and packages.
- Accepts multiple include paths (`-I`). Each path is expanded to include all
  subdirectories, so include files can be found anywhere under the specified dir.
- Optionally generates absolute paths with `--absolute_path`.
- File list includes modules only once to avoid recompilation issues.
- Optionally generates `+incdir+<dir>` lines for every directory with a discovered
  file, using the `--include_incdirs` switch. This helps simulators/tools find
  all include directories automatically.

**Requirements**
- Python 3.8+ (or your system `python3`).
- The `svinst` package. See [pysvinst](https://github.com/sgherbst/pysvinst).

**Limitations**
- No specific limitations for include directories; both file and incdir
  discovery are supported.

**Quick start**

```
python3 generateRtlFileList.py <path/to/top.sv>
```

The script writes `<topmodule>.f` in the current directory, where `<topmodule>`
is the top-level module name parsed from the input file.

**Usage examples**

- Basic:

```
python3 generateRtlFileList.py examples/jtag/rtl/jtag.sv
```

- Provide include directories (repeat `-I` as needed; all subdirs included):

```
python3 generateRtlFileList.py examples/multipleDirs/rtl/top.sv \
  -I examples/multipleDirs/rtl
```

- Generate absolute paths in the `.f`:

```
python3 generateRtlFileList.py examples/jtag/rtl/jtag.sv --absolute_path
```

- Generates `+incdir+<dir>` lines for every directory with a discovered file:

```
python3 generateRtlFileList.py examples/multipleDirs/rtl/top.sv --include_incdirs
```

**Behavior details**
- With `--absolute_path`, the script writes absolute paths for all discovered
  files (one per line) into the `.f`.
- Without `--absolute_path`, paths are relative to the top-level module dir.
  Example output for `top.sv`:

```
top.sv
ip1/ip1.sv
ip2/ip2.sv
```

- If a submodule file isn't in the instantiating file's dir, the script searches
  each `-I` include dir recursively (using `os.walk`). All subdirs of each `-I`
  path are included. The entry is still relative to the top-level dir unless
  `--absolute_path` is used.

- With `--include_incdirs`, the script generates a `+incdir+<dir>` line before
  any file from a new dir is listed. This helps simulators/tools find all include
  dirs automatically.

**Help**

```
python3 generateRtlFileList.py -h
```

NOTE
----
The code is entirely written using AI!
