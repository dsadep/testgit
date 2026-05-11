import sys

from catfile.func import CatFile


def run(args):
    try:
        CatFile.cat_file(args.mode, args.hash_prefix)
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(1)