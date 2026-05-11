import os

from utils import write_file


class Init:
    def init(repo):
        os.mkdir(repo)
        os.mkdir(os.path.join(repo, '.git'))
        for name in ['objects', 'refs', 'refs/heads']:
            os.mkdir(os.path.join(repo, '.git', name))
        write_file(os.path.join(repo, '.git', 'HEAD'),
                b'ref: refs/heads/master')
        print('Initialized empty repository: {}'.format(repo))