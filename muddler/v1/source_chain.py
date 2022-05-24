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
import os


class SourceChain(object):
    def __init__(self, source_fps):
        self._fps = source_fps.copy()
        self._key_size = sum([
            os.fstat(kfp.fileno()).st_size for kfp in self._fps])
        self.reset()

    def reset(self):
        self._cur_file_ndx = 0
        self._hash = hashlib.new('sha512')

        for kfp in self._fps:
            kfp.seek(0, 0)

    def read_block(self, block_size):
        if block_size <= 0:
            return b''

        buf = bytearray(block_size)
        buf_filled = 0

        block = self._fps[self._cur_file_ndx].read(block_size)
        buf[0:len(block)] = block
        buf_filled += len(block)

        while buf_filled < block_size:
            self._cur_file_ndx += 1
            if self._cur_file_ndx >= len(self._fps):
                self.reset()

            to_read = block_size - buf_filled
            block = self._fps[self._cur_file_ndx].read(to_read)
            blen = len(block)
            buf[buf_filled: buf_filled + blen] = block
            buf_filled += blen

        dsize = self._hash.digest_size
        cur_ndx = 0

        while cur_ndx < block_size:
            bleft = block_size - cur_ndx
            if bleft >= dsize:
                self._hash.update(buf[cur_ndx:cur_ndx+dsize])
                buf[cur_ndx:cur_ndx+dsize] = self._hash.digest()
                cur_ndx += dsize
            else:
                self._hash.update(buf[cur_ndx:])
                buf[cur_ndx:] = self._hash.digest()[:bleft]
                cur_ndx += bleft

        return bytes(buf)

    @property
    def size(self):
        return self._key_size
