"""Write a release zip with forward-slash entry names, laid out from the game root.

usage: python make_zip.py <zip path> <game-root folder> <relative file>...
"""
import os
import sys
import zipfile


def main(zip_path, root, files):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.write(os.path.join(root, rel), rel.replace('\\', '/'))


if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
