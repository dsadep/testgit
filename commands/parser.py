   
import argparse

from commands.runners.ls_files import run as run_ls_files
from commands.runners.init import run as run_init
from commands.runners.add import run as run_add
from commands.runners.hash_object import run as run_hash_object
from commands.runners.status import run as run_status
from commands.runners.diff import run as run_diff
from commands.runners.commit import run as run_commit
from commands.runners.cat_file import run as run_cat_file
from commands.runners.push import run as run_push

class Parser:
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest='command', metavar='command')
    sub_parsers.required = True


    sub_parser = sub_parsers.add_parser(
        'add',
        help='add file(s) to index'
        )
    sub_parser.add_argument(
        'paths', nargs='+',
        metavar='path',
        help='path(s) of files to add'
        )
    sub_parser.set_defaults(func=run_add)


    sub_parser = sub_parsers.add_parser(
        'cat-file',
        help='display contents of object'
        )
    valid_modes = ['commit', 'tree', 'blob', 'size', 'type', 'pretty']
    sub_parser.add_argument(
        'mode', choices=valid_modes,
        help='object type (commit, tree, blob) or display mode (size, type, pretty)'
        )
    sub_parser.add_argument(
        'hash_prefix',
        help='SHA-1 hash (or hash prefix) of object to display'
        )
    sub_parser.set_defaults(func=run_cat_file)


    sub_parser = sub_parsers.add_parser(
        'commit',
        help='commit current state of index to master branch'
        )
    sub_parser.add_argument(
        '-a', '--author',
        help='commit author in format "A U Thor <author@example.com>" '
                 '(uses GIT_AUTHOR_NAME and GIT_AUTHOR_EMAIL environment '
                 'variables by default)'
                )
    sub_parser.add_argument(
        '-m', '--message', 
        required=True,
        help='text of commit message'
        )
    sub_parser.set_defaults(func=run_commit)


    sub_parser = sub_parsers.add_parser(
        'diff',
        help='show diff of files changed (between index and working copy)'
        )
    sub_parser.set_defaults(func=run_diff)


    sub_parser = sub_parsers.add_parser(
        'hash-object',
        help='hash contents of given path (and optionally write to object store)'
        )
    sub_parser.add_argument(
        'path',
        help='path of file to hash'
        )
    sub_parser.add_argument(
        '-t', choices=['commit', 'tree', 'blob'],
        default='blob', dest='type',
        help='type of object (default %(default)r)'
        )
    sub_parser.add_argument(
        '-w', action='store_true', 
        dest='write',
        help='write object to object store (as well as printing hash)'
        )
    sub_parser.set_defaults(func=run_hash_object)


    sub_parser = sub_parsers.add_parser(
        'init',
        help='initialize a new repo'
        )
    sub_parser.add_argument(
        'repo',
        help='directory name for new repo'
        )
    sub_parser.set_defaults(func=run_init)


    sub_parser = sub_parsers.add_parser(
        'ls-files',
        help='list files in index'
        )
    sub_parser.add_argument(
        '-s', '--stage', 
        action='store_true',
        help='show object details (mode, hash, and stage number) in addition to path'
        )
    sub_parser.set_defaults(func=run_ls_files)


    sub_parser = sub_parsers.add_parser(
        'status',
        help='show status of working copy'
        )
    sub_parser.set_defaults(func=run_status)



    sub_parser = sub_parsers.add_parser(
        'push',
        help='push master branch to given git server URL'
        )
    sub_parser.add_argument(
        'git_url',
        help='URL of git repo, eg: https://github.com/benhoyt/pygit.git'
        )
    sub_parser.add_argument(
        '-p', '--password',
        help='password to use for authentication (uses GIT_PASSWORD environment variable by default)'
        )
    sub_parser.add_argument(
        '-u', '--username',
        help='username to use for authentication (uses GIT_USERNAME environment variable by default)'
        )
    sub_parser.set_defaults(func=run_push)