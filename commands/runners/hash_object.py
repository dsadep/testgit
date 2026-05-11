from utils import read_file
from hash_obj.func import HashObject


def run(args):
    print(HashObject.hash_object(read_file(args.path), args.type, write=args.write))