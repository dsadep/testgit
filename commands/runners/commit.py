from commit.func import Commit

def run(args):
    Commit.commit(args.message, author=args.author)