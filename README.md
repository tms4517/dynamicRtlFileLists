# Dynamic RTL File Lists

Dynamically generate file-list (`.f`) files for SystemVerilog projects.

**Purpose:**
- Discover module/package source files starting from a top-level
  SystemVerilog file and generate an ordered `.f` file suitable for
  simulators or other tools that accept Verilog filelists.

**Features:**
- Recursively discovers instantiated modules and packages.
- Accepts include paths (`-I`) and searches them recursively for
  submodule files.
- Optionally generates absolute paths with `--absolute_path`.

**Requirements**
- Python 3.8+ (or your system `python3`).
- The `svinst` package must be available on `PYTHONPATH` (the script
  uses `svinst.get_defs`). See https://github.com/sgherbst/pysvinst.

**Quick start**
1. From the project root run (preferred new name):

```
python3 generateRtlFileList.py <path/to/top.sv>
```

The old name is still supported as a wrapper for backward compatibility:

```
python3 getModules.py <path/to/top.sv>
```

2. The script writes a file named `<topmodule>.f` in the current
   directory (where `<topmodule>` is the top-level module name parsed
   from the input file).

**Usage examples**

- Basic:

```
python3 generateRtlFileList.py examples/jtag/rtl/jtag.sv
```

- Provide include directories (repeat `-I` as needed):

```
python3 generateRtlFileList.py examples/multipleDirs/rtl/top.sv \
  -I examples/multipleDirs/rtl
```

- generate absolute paths in the generated `.f`:

```
python3 generateRtlFileList.py examples/jtag/rtl/jtag.sv --absolute_path
```

**Behavior details**
- When `--absolute_path` is provided the script writes absolute paths
  for all discovered files (one per line) into the generated `.f`.
- When `--absolute_path` is not provided the script writes paths
  relative to the top-level module directory. Example output for
  `top.sv` may look like:

```
top.sv
ip1/ip1.sv
ip2/ip2.sv
```

- If a submodule file isn't present in the instantiating file's
  directory, the script searches each `-I` include directory
  recursively (using `os.walk`) and uses the found file for parsing.
  The printed entry is still relative to the top-level directory
  unless `--absolute_path` is used.

**Output file name**
- By default the output file is named `<topmodule>.f`.

**Troubleshooting**
- If parsing fails for a file `getModules.py` prints a warning to
  `stderr` and continues.
- If a submodule source file cannot be located the script prints a
  `Note:` to `stderr` and still generates the path where the file would be
  expected.

**Help**

```
python3 generateRtlFileList.py -h
```

Or call the compatibility wrapper:

```
python3 getModules.py -h
```
