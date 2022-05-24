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


from contextlib import ExitStack
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from muddler.utils import hash_file_sha256, open_files_in_stack
from muddler.v1 import Muddle_V1
from muddler.v1.source_chain import SourceChain


class MuddleException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Muddling Error: {}'.format(self.msg)


def compute_sources_entries(manifest, config, src_path):
    source_entries = {}

    if config['source_type'] == 'file':
        sourcef_path = Path(src_path)
        if not sourcef_path.is_file():
            raise MuddleException(
                'Source path {} is not a valid file.'.format(
                    str(repr(sourcef_path))))

        with open(sourcef_path, 'rb') as source_fp:
            source_hash = hash_file_sha256(source_fp)

        source_entries['/'] = {
            'hash': source_hash,
            'size': sourcef_path.stat().st_size
        }

    else:
        # Get unique list of sources from config
        source_set = set([])
        for target, sources in config['targets'].items():
            source_set.update(sources)

        for sourcef in source_set:
            sourcef_path = Path(src_path, sourcef)

            if not sourcef_path.is_file():
                raise MuddleException(
                    'Source path {} is not a valid file.'.format(
                        repr(str(sourcef_path))))

            with open(sourcef_path, 'rb') as source_fp:
                source_hash = hash_file_sha256(source_fp)

            source_entries[sourcef] = {
                'hash': source_hash,
                'size': sourcef_path.stat().st_size
            }

    manifest['sources'] = source_entries


def compute_targets_entries(manifest, config, trg_path):
    target_entries = {}

    if config['target_type'] == 'file':
        targetf_path = Path(trg_path)
        if not targetf_path.is_file():
            raise MuddleException(
                'Target path {} is not a valid file.'.format(
                    str(repr(targetf_path))))

        with open(targetf_path, 'rb') as target_fp:
            target_hash = hash_file_sha256(target_fp)

        if config['source_type'] == 'file':
            sources = ['/']
        else:
            sources = config['targets']['/']

        target_entries['/'] = {
            'hash': target_hash,
            'sources': sources,
            'size': targetf_path.stat().st_size
        }

    else:
        for targetf in config['targets']:
            targetf_path = Path(trg_path, targetf)
            if not targetf_path.is_file():
                raise MuddleException(
                    'Target path {} is not a valid file.'.format(
                        str(repr(targetf_path))))

            with open(targetf_path, 'rb') as target_fp:
                target_hash = hash_file_sha256(target_fp)

            if config['source_type'] == 'file':
                sources = ['/']
            else:
                sources = config['targets'][targetf]

            target_entries[targetf] = {
                'hash': target_hash,
                'sources': sources,
                'size': targetf_path.stat().st_size
            }

    manifest['targets'] = target_entries


def generate_manifest(config, src_path, trg_path, out_path):
    manifest = {
        'algorithm_version': config['algorithm_version'],
        'source_type': config['source_type'],
        'target_type': config['target_type'],
        'sources': {},
        'targets': {}
    }

    compute_sources_entries(manifest, config, src_path)
    compute_targets_entries(manifest, config, trg_path)

    return manifest


def generate_muddled_files(manifest, src_path, trg_path, out_path):
    if manifest['target_type'] == 'file':
        targetf_path = Path(trg_path)
        outputf_path = Path(out_path, 'muddled')
        target_info = manifest['targets']['/']

        if manifest['source_type'] == 'file':
            sources = [Path(src_path)]
        else:
            sources = [Path(src_path, s) for s in target_info['sources']]

        with ExitStack() as estack:
            target_fp = estack.enter_context(open(targetf_path, 'rb'))
            output_fp = estack.enter_context(open(outputf_path, 'wb'))
            source_fps = open_files_in_stack(estack, sources, 'rb')
            schain = SourceChain(source_fps)
            muddler = Muddle_V1(schain)
            muddler.muddle_file(target_fp, output_fp)

        with open(outputf_path, 'rb') as output_fp:
            target_info['muddled_hash'] = hash_file_sha256(output_fp)

    else:
        for targetf, target_info in manifest['targets'].items():
            targetf_path = Path(trg_path, targetf)
            outputf_path = Path(out_path, 'muddled', targetf)
            target_info = manifest['targets'][targetf]

            if manifest['source_type'] == 'file':
                sources = [Path(src_path)]
            else:
                sources = [Path(src_path, s) for s in target_info['sources']]

            with ExitStack() as estack:
                target_fp = estack.enter_context(open(targetf_path, 'rb'))
                outputf_path.parent.mkdir(parents=True, exist_ok=True)
                output_fp = estack.enter_context(open(outputf_path, 'wb'))
                source_fps = open_files_in_stack(estack, sources, 'rb')
                schain = SourceChain(source_fps)
                muddler = Muddle_V1(schain)
                muddler.muddle_file(target_fp, output_fp)

            with open(outputf_path, 'rb') as output_fp:
                target_info['muddled_hash'] = hash_file_sha256(output_fp)


def package_muddled_files(manifest, tmp_output, out_path):
    manifest_json = json.dumps(manifest)

    try:
        with ZipFile(out_path, 'w') as package:
            package.writestr('manifest.json', manifest_json)

            if manifest['target_type'] == 'file':
                muddle_path = Path(tmp_output, 'muddled')
                package.write(muddle_path, 'muddled')
            else:
                for target in manifest['targets']:
                    muddle_path = Path(tmp_output, 'muddled', target)
                    package.write(muddle_path, Path('muddled', target))
    # TODO: More fine-grained exception handeling.
    except Exception:
        raise MuddleException('Could not write muddled output.')


def muddle(config, src, trg, output):
    src_path = Path(src)
    trg_path = Path(trg)
    out_path = Path(output)

    if config['source_type'] == 'dir' and not src_path.is_dir():
        raise MuddleException(
            'Source type is specified as \'dir\' but given source is not a '
            'directory.')

    if config['source_type'] == 'file' and not src_path.is_file():
        raise MuddleException(
            'Source type is specified as \'file\' but given source is not a '
            'file.')

    if config['target_type'] == 'dir' and not trg_path.is_dir():
        raise MuddleException(
            'Target type is specified as \'dir\' but given target is not a '
            'directory.')

    if config['target_type'] == 'file' and not trg_path.is_file():
        raise MuddleException(
            'Target type is specified as \'file\' but given target is not a '
            'file.')

    if out_path.is_dir():
        raise MuddleException(
            'Provided output path is an existing directory.')

    manifest = generate_manifest(config, src_path, trg_path, out_path)

    with TemporaryDirectory() as tmp_output:
        generate_muddled_files(manifest, src_path, trg_path, tmp_output)
        package_muddled_files(manifest, tmp_output, out_path)
