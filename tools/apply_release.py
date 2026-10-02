"""Verify the source and patch, decode, then verify and publish the result."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify(path, expected):
    if path.stat().st_size != expected['bytes']:
        raise ValueError(f'Unexpected size: {path.name}')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    if digest.hexdigest() != expected['sha256']:
        raise ValueError(f'SHA-256 mismatch: {path.name}')
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('xdelta', 'source', 'patch', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    source, patch, output = (getattr(args, n).resolve() for n in ('source', 'patch', 'output'))
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((ROOT / 'release_manifest.json').read_text(encoding='utf-8'))
    verify(source, manifest['source'])
    verify(patch, manifest['patch'])
    fd, temporary = tempfile.mkstemp(prefix='patch-', suffix='.iso', dir=output.parent)
    os.close(fd)
    staged = Path(temporary)
    try:
        cwd = Path(os.path.commonpath([source.parent, patch.parent, output.parent]))
        rel = lambda p: os.path.relpath(p, cwd)
        subprocess.run([str(args.xdelta.resolve()), '-d', '-f', '-s', rel(source), rel(patch), rel(staged)], cwd=cwd, check=True)
        digest = verify(staged, manifest['output'])
        # Exclusive creation prevents accidentally replacing another file.
        os.link(staged, output)
        print('Verified output SHA-256:', digest)
    finally:
        staged.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
