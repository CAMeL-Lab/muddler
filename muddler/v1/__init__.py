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


from ..utils import xor_bytes


BLOCK_SIZE = 1024


class Muddle_V1(object):
    def __init__(self, source_chain, block_size=BLOCK_SIZE):
        self._source_chain = source_chain
        self._block_size = block_size

    def muddle_file(self, input_fp, output_fp):
        self._block_size = max(self._block_size, 1)
        self._source_chain.reset()
        buf = bytearray(input_fp.read())
        buf_size = len(buf)
        key_size = self._source_chain.size
        mbytes = max(buf_size, key_size)
        buf_ndx = 0

        while mbytes > 0:
            buf_left = buf_size - buf_ndx
            key_len = min(mbytes, self._block_size, buf_left)
            key_block = self._source_chain.read_block(key_len)

            buf_block = buf[buf_ndx:buf_ndx+key_len]
            buf[buf_ndx:buf_ndx+key_len] = xor_bytes(key_block, buf_block)

            buf_ndx = (buf_ndx + key_len) % buf_size
            mbytes -= key_len

        output_fp.write(buf)
