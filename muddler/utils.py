# MIT License
#
# Copyright 2020-2022 New York University Abu Dhabi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import hashlib


DEFAULT_BLOCK_SIZE = 65536


def hash_file_sha256(fp, block_size=DEFAULT_BLOCK_SIZE):
    m = hashlib.sha256()

    buf = fp.read(block_size)

    while len(buf) > 0:
        m.update(buf)
        buf = fp.read(block_size)

    return m.hexdigest()


def xor_bytes(bstr1, bstr2):
    return bytes([_a ^ _b for _a, _b in zip(bstr1, bstr2)])


def open_files_in_stack(stack, paths, mode):
    files = []

    for path in paths:
        files.append(stack.enter_context(open(path, mode)))

    return files
