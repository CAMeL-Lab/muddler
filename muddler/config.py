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


TARGET_SOURCE_TYPES = ['dir', 'file']
ALGORITHM_VERSIONS = ['1']


class MuddlerConfigException(Exception):
    def __init__(self, line_num, msg):
        self.line_num = line_num
        self.msg = msg

    def __str__(self):
        return 'Mudller Config Error [line {}]: {}'.format(self.line_num,
                                                           self.msg)


def parse_config(fp):
    line_no = 0

    target_type = None
    source_type = None
    algorithm_version = None
    targets = {}

    # Parser state
    curr_target = None
    curr_sources = None
    header_is_done = False

    for line in fp:
        line = line[:-1].lstrip()
        line_no += 1

        if len(line) == 0:
            continue

        elif line.startswith('-'):
            continue

        elif line.startswith('##'):
            # Make sure header info isn't declared past the start of the file
            if header_is_done:
                raise MuddlerConfigException(
                    line_no,
                    'Adding header info in middle of file.')

            tokens = line.split(maxsplit=1)

            if tokens[0] == '##TARGET_TYPE':
                if tokens[1] in TARGET_SOURCE_TYPES:
                    target_type = tokens[1]
                else:
                    raise MuddlerConfigException(
                        line_no,
                        'Invalid value for TARGET_TYPE ({})'.format(
                            repr(tokens[1])))
            elif tokens[0] == '##SOURCE_TYPE':
                if tokens[1] in TARGET_SOURCE_TYPES:
                    source_type = tokens[1]
                else:
                    raise MuddlerConfigException(
                        line_no,
                        'Invalid value for SOURCE_TYPE ({})'.format(
                            repr(tokens[1])))
            elif tokens[0] == '##ALGORITHM_VERSION':
                if tokens[1] in ALGORITHM_VERSIONS:
                    algorithm_version = tokens[1]
                else:
                    raise MuddlerConfigException(
                        line_no,
                        'Invalid value for ALGORITHM_VERSION ({})'.format(
                            repr(tokens[1])))
            else:
                raise MuddlerConfigException(
                    line_no,
                    'Invalid header variable {}.'.format(repr(tokens[0][2:])))

        elif line.startswith('#'):
            header_is_done = True
            if algorithm_version is None:
                raise MuddlerConfigException(
                    line_no,
                    'Missing ALGORITHM_VERSION in header.')
            if target_type is None:
                raise MuddlerConfigException(
                    line_no,
                    'Missing TARGET_TYPE in header.')
            if source_type is None:
                raise MuddlerConfigException(
                    line_no,
                    'Missing SOURCE_TYPE in header.')

            tokens = line.split(maxsplit=1)

            if tokens[0] == '#TARGET':

                if len(tokens) != 2:
                    raise MuddlerConfigException(
                        line_no,
                        'Invalid TARGET line.')

                if curr_target is not None:
                    if source_type == 'dir' and len(curr_sources) == 0:
                        raise MuddlerConfigException(
                            line_no,
                            'No sources provided for target {}.'.format(
                                repr(curr_target)))
                    if target_type == 'dir':
                        targets[curr_target[1:]] = curr_sources
                    else:
                        targets[curr_target] = curr_sources

                curr_target = tokens[1]

                if target_type == 'file' and curr_target != '/':
                    raise MuddlerConfigException(
                        line_no,
                        'Expecting target name \'/\' for taget type "file".')
                if target_type == 'dir' and curr_target == '/':
                    raise MuddlerConfigException(
                        line_no,
                        'Invalid target name \'/\' for taget type "dir".')
                if curr_target in targets:
                    raise MuddlerConfigException(
                        line_no,
                        'Duplicate entry for target {}.'.format(
                            repr(curr_target)))

                if source_type == 'file':
                    curr_sources = None
                else:
                    curr_sources = []

            else:
                raise MuddlerConfigException(line_no, 'Invalid config syntax.')

        elif line.startswith('/'):
            if source_type == 'file':
                # TODO: Provide a better error message.
                raise MuddlerConfigException(
                    line_no,
                    'Source line provided when source type is "file".')
            if line in curr_sources:
                raise MuddlerConfigException(line_no, 'Duplicate source line.')
            curr_sources.append(line[1:])

        else:
            raise MuddlerConfigException(line_no, 'Invalid config syntax.')

    if curr_target is not None:
        if source_type == 'dir' and len(curr_sources) == 0:
            raise MuddlerConfigException(
                line_no,
                'No sources provided for target {}.'.format(
                    repr(curr_target)))
        if target_type == 'dir':
            targets[curr_target[1:]] = curr_sources
        else:
            targets[curr_target] = curr_sources

    config = {
        "algorithm_version": algorithm_version,
        "target_type": target_type,
        "source_type": source_type,
        "targets": targets
    }

    return config
