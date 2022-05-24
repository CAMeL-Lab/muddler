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


class UnmuddleException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Unmuddling Error: {}'.format(self.msg)


def extract_package(package_path, extracted_path):
    try:
        with ZipFile(package_path, 'r') as package:
            package.extractall(path=extracted_path)
    except Exception:
        UnmuddleException('Could not extract muddled content.')


def validate_manifest(manifest):
    # TODO: Use JSON schema to validate manifest
    pass


def validate_package(manifest, extracted_path):
    muddled_path = Path(extracted_path, 'muddled')

    if (manifest['target_type'] == 'file' and not muddled_path.is_file() or
            manifest['target_type'] == 'dir' and not muddled_path.is_dir()):
        raise UnmuddleException('Invalid or corrupt muddled package.')

    if manifest['target_type'] == 'file':
        with open(muddled_path, 'rb') as muddled_fp:
            muddled_hash = hash_file_sha256(muddled_fp)

        if muddled_hash != manifest['targets']['/']['muddled_hash']:
            raise UnmuddleException('Invalid or corrupt muddled package.')

    else:
        for target in manifest['targets']:
            muddledf_path = Path(muddled_path, target)
            with open(muddledf_path, 'rb') as muddled_fp:
                muddled_hash = hash_file_sha256(muddled_fp)

            if muddled_hash != manifest['targets'][target]['muddled_hash']:
                raise UnmuddleException('Invalid or corrupt muddled package.')


def validate_sources(manifest, source_path):
    if manifest['source_type'] == 'file' and not source_path.is_file():
        raise UnmuddleException('Provided source is not a file.')
    if manifest['source_type'] == 'dir' and not source_path.is_dir():
        raise UnmuddleException('Provided source is not a directory.')

    if manifest['source_type'] == 'file':
        with open(source_path, 'rb') as source_fp:
            source_hash = hash_file_sha256(source_fp)

        if source_hash != manifest['sources']['/']['hash']:
            raise UnmuddleException('Invalid source file for muddled package.')

    else:
        for source in manifest['sources']:
            sourcef_path = Path(source_path, source)
            with open(sourcef_path, 'rb') as source_fp:
                source_hash = hash_file_sha256(source_fp)

            if source_hash != manifest['sources'][source]['hash']:
                raise UnmuddleException(
                    'Invalid source file for muddled package.')


def generate_targets(manifest, source_path, extracted_path, target_path):
    muddled_path = Path(extracted_path, 'muddled')

    if manifest['target_type'] == 'file':
        if manifest['source_type'] == 'file':
            sources = [source_path]
        else:
            sources_sub = manifest['targets']['/']['sources']
            sources = [Path(source_path, s) for s in sources_sub]

        with ExitStack() as estack:
            target_fp = estack.enter_context(open(target_path, 'wb'))
            muddled_fp = estack.enter_context(open(muddled_path, 'rb'))
            source_fps = open_files_in_stack(estack, sources, 'rb')
            schain = SourceChain(source_fps)
            muddler = Muddle_V1(schain)
            muddler.muddle_file(muddled_fp, target_fp)
    else:
        for target in manifest['targets']:
            if manifest['source_type'] == 'file':
                sources = [source_path]
            else:
                sources_sub = manifest['targets'][target]['sources']
                sources = [Path(source_path, s) for s in sources_sub]

            with ExitStack() as estack:
                targetf_path = Path(target_path, target)
                muddledf_path = Path(muddled_path, target)
                targetf_path.parent.mkdir(parents=True, exist_ok=True)
                target_fp = estack.enter_context(open(targetf_path, 'wb'))
                muddled_fp = estack.enter_context(open(muddledf_path, 'rb'))
                source_fps = open_files_in_stack(estack, sources, 'rb')
                schain = SourceChain(source_fps)
                muddler = Muddle_V1(schain)
                muddler.muddle_file(muddled_fp, target_fp)


def validate_targets(manifest, target_path):
    # TODO: Also validate file size?

    if manifest['target_type'] == 'file':
        with open(target_path, 'rb') as target_fp:
            target_hash = hash_file_sha256(target_fp)
            if target_hash != manifest['targets']['/']['hash']:
                raise UnmuddleException(
                    'Target hash mismatch for file {}.'.format(
                        repr(target_path)))
    else:
        for target, target_info in manifest['targets'].items():
            targetf_path = Path(target_path, target)
            with open(targetf_path, 'rb') as target_fp:
                target_hash = hash_file_sha256(target_fp)
                if target_hash != target_info['hash']:
                    raise UnmuddleException(
                        'Target hash mismatch for file {}.'.format(
                            repr(targetf_path)))


def unmuddle(src, muddled, trg):
    source_path = Path(src)
    muddled_path = Path(muddled)
    target_path = Path(trg)

    with TemporaryDirectory() as tmp_extracted:
        extracted_path = Path(tmp_extracted)

        extract_package(muddled_path, extracted_path)

        try:
            manifest_path = Path(tmp_extracted, 'manifest.json')
            with open(manifest_path, 'r') as manifest_fp:
                manifest = json.load(manifest_fp)
        except Exception:
            raise UnmuddleException('Invalid or corrupt muddled package.')

        validate_manifest(manifest)

        try:
            validate_package(manifest, extracted_path)
        except Exception:
            raise UnmuddleException('Invalid or corrupt muddled package.')

        try:
            validate_sources(manifest, source_path)
        except FileNotFoundError as e:
            raise UnmuddleException(
                'Could not read source file {}'.format(repr(e.filename)))
        except IsADirectoryError as e:
            raise UnmuddleException(
                'Could not read source file {}'.format(repr(e.filename)))

        generate_targets(manifest, source_path, tmp_extracted, target_path)
        validate_targets(manifest, target_path)
