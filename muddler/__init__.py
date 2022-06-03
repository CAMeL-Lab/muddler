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


"""The Muddler derived-file sharing utility.

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
"""


import docopt
import os
from pathlib import Path
import sys
import traceback

from muddler.config import parse_config, MuddlerConfigException
from muddler.muddle import muddle, MuddleException
from muddler.unmuddle import unmuddle, UnmuddleException


try:
    _VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(_VERSION_FILE) as version_fp:
        __version__ = version_fp.read().strip()
except Exception:
    __version__ = '???'


def muddle_command(arguments):
    print('Muddling...')

    src_path = Path(arguments['-s'])
    trg_path = Path(arguments['-t'])
    muddle_path = Path(arguments['<MUDDLED_PATH>'])

    if arguments['-c'] is None:
        if not src_path.is_file():
            pass
        if not trg_path.is_file():
            pass

        config = {
            'algorithm_version': '1',
            'source_type': 'file',
            'target_type': 'file',
            'targets': {'/': None}
        }

    else:
        config_path = Path(arguments['-c'])

        try:
            with open(config_path, 'r') as config_fp:
                config = parse_config(config_fp)
        except MuddlerConfigException as m:
            print('[Config Error]', str(m))
            sys.exit(1)

    try:
        muddle(config, src_path, trg_path, muddle_path)
    except MuddleException as m:
        if os.environ('MUDDLER_DEBUG'):
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        else:
            print(str(m))
            sys.exit(1)
    except Exception:
        if os.environ('MUDDLER_DEBUG'):
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        else:
            print('An error occured while unmuddling file.')
            sys.exit(1)


def unmuddle_command(arguments):
    print('Unmuddling....')

    src_path = Path(arguments['-s'])
    muddled_path = Path(arguments['-m'])
    target_path = Path(arguments['<TARGET_OUT>'])

    try:
        unmuddle(src_path, muddled_path, target_path)
    except UnmuddleException as m:
        if os.environ('MUDDLER_DEBUG'):
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        else:
            print(str(m))
            sys.exit(1)
    except Exception:
        if os.environ('MUDDLER_DEBUG'):
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        else:
            print('An error occured while unmuddling file.')
            sys.exit(1)


def main():
    arguments = docopt.docopt(__doc__, version=__version__)

    if arguments['muddle']:
        muddle_command(arguments)
    elif arguments['unmuddle']:
        unmuddle_command(arguments)


if __name__ == '__main__':
    main()
