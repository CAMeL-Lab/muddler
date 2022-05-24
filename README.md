# Muddler

## About

Muddler is a tool for sharing derived data.

It is sometimes necessary to share data publicly that has been derived from a
non-public source without sharing the source itself.
Muddler solves this issue by "subtracting" the source data from the target
(or derived) data, a process we call *muddling*.
This generates a *muddled package* that can be distributed publicly.
In order to retrieve the target data, users must first acquire the derived data
through proper channels and can then *unmuddle* the *muddled package* through
Muddler to generate the target data.

This is particularly useful when the derived data cannot be trivially
reconstructd from the source data such as human annotated/modified data.

**Please make sure that the source license permits creating derived work!**

## Installation

Muddler requires Python 3.6+ to install.

To install using pip, just run:

```bash
pip install muddler
```

## Usage

```text
Usage: muddler muddle -s <SRC_PATH> -t <TRG_PATH> <MUDDLED_PATH>
       muddler muddle -c <CONFIG> -s <SRC_PATH> -t <TRG_PATH> <MUDDLED_PATH>
       muddler unmuddle -s <SRC_FILE> -m <MUDDLED_PATH> <TARGET_OUT>
       muddler (-h | --help)
       muddler (-v | --version)

Options:
    -h, --help
        Print help message.
    -v, --version
        Print muddler version
    -c <CONFIG>
        Path to muddler config file.
    -s <SRC_PATH>
        Path to source file or directory. When <CONFIG> is not specified in
        muddle mode, SRC_PATH must point to a file and not a directory.
    -t <TRG_PATH>
        Path to target file or directory. When <CONFIG> is not specified in
        muddle mode, TRG_PATH must point to a file and not a directory.
    -m <MUDDLED_PATH>
        Path to muddled package to be unmuddled.
```

Muddler runs two modes: muddle mode for generating muddled packages,
and unmuddle mode to extract targets from a muddled file.

### Muddle Mode

The simplest example for muddling is when both the source and the target are
single files.

For example:

```bash
muddler muddle -s /path/to/source_file -t /path/to/target_file /path/to/my_package.muddle
```

Note that the muddled package doesn't have to end with the *.muddle* extension.

When at least one of either the source or target is a directory (ie the source
data is composed of multiple files), we must additionally pass a config file to
muddler.

For example:

```bash
muddler muddle -c /path/to/config_file -s /path/to/source_dir -t /path/to/target_file /path/to/my_package.muddle
```

The config file provides muddler with a mapping on which source file(s) where
used to derive the target(s). See the [Config Format](#config-format) section
for more information.

### Unmuddle Mode

To unmuddle a muddled package, one must first acquire the source files from
which the muddled data is derived from. The acquired source file or directory
must be exactly the same both in directory structure, file names, and
file contents (byte for byte).

Once the source files have been acquired, the muddled package can be
unmuddled by running:

```bash
muddler unmuddle -s /path/to/source -m /path/to/my_package.muddle /path/to/target_output
```

The generated target will either be a single file or a directory depending on
the target used for muddling.

## Config Format

Below is a documented configuration file that structure in general:

```text
- This is a comment! All comments begin with '-' must be on their own individual lines.
- Comments are ignored by muddler and are used for documentation and organizational purposes.
    - Comments can be preceeded by whitespace as well.

- The first section in a config file is a header that tells muddler what kind of source and
- target to expect as well as which muddling algorithm to use.

- The TARGET_TYPE and SOURCE_TYPE headers tell muddler whether to expect a file or directory
- for target and source respectively. A value of 'file' indicates a single file, while 'dir'
- indicates a directory.
##TARGET_TYPE dir
##SOURCE_TYPE dir

- The algorithm version tells muddler what algorithm to use to create the muddled package.
- At the moment only one algorithm ('1') is available but the field is required for backwards
- compatibility when new algorithms are added.
##ALGORITHM_VERSION 1


- After specifying the header, we can start specifying targets and their respective sources.
- For a 'dir' target, each target entry consists of a relative path within the target directory.
- For example, if the absolut path to the target directory is '/home/username/target', then
- the below target entry specifies source for the file at '/home/username/target/target_01.txt'.
- Note that each target path MUST start with '/'.
- All speaces after #TARGET and the first '/' character are ignored, but there needs
- to be at least one.
- Note that any whitespace at the end of a line is NOT IGNORED.
- This is because valid filenames can include whitespace.
#TARGET   /target_01.txt
    - Each target must provide a list of sources used to derive it.
    - This list has to be unique.
    - Similar to targets, each source is a relative path to a file within the source directory.
    - They must also start with a '/' character and proceeding whitespaces are NOT IGNORED.
    - Preceeding whitespace is ignored though.
    /source_01.txt
    /source_02.txt

- Both target and source paths can point to files in subdirectories.
#TARGET   /sub/target_02.txt
    /source_01.txt
    /sub/source_03.txt

- Each target entry must have a unique target path.
- So adding the following entry would cause an error:
#TARGET   /target_01.txt
    /source_01.txt
    /source_02.txt
```

Additional rules apply when either target or source are single files.

When target is a single file, the config file should include only one target entry where the
target path is '/' as so:

```text
##TARGET_TYPE file
##SOURCE_TYPE dir
##ALGORITHM_VERSION 1

#TARGET   /
    /source_01.txt
    /source_02.txt
```

If source is a single file then target entries should not be followed by any source lines as so:

```text
##TARGET_TYPE dir
##SOURCE_TYPE file
##ALGORITHM_VERSION 1

#TARGET   /target_01.txt
#TARGET   /target_02.txt
#TARGET   /sub/target_03.txt
```

## License

Muddler is available under the MIT license.
See the [LICENSE](/LICENSE) file for more info.

## Contributors

- [Ossama Obeid](https://github.com/owo)
- [Nizar Habash](https://github.com/nizarhabash1)
