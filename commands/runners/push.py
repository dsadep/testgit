from push.func import Push


def run(args):
    Push.push(args.git_url, username=args.username, password=args.password)