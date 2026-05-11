import os
import time

from utils import get_local_master_hash, hash_obj, write_file, write_tree

class Commit:
    def commit(message, author=None):
        tree = write_tree()
        parent = get_local_master_hash()
        if author is None:
            author = '{} <{}>'.format(
                    os.getenv('GIT_AUTHOR_NAME'), os.getenv('GIT_AUTHOR_EMAIL'))
        timestamp = int(time.mktime(time.localtime()))
        utc_offset = -time.timezone
        author_time = '{} {}{:02}{:02}'.format(
                timestamp,
                '+' if utc_offset > 0 else '-',
                abs(utc_offset) // 3600,
                (abs(utc_offset) // 60) % 60)
        lines = ['tree ' + tree]
        if parent:
            lines.append('parent ' + parent)
        lines.append('author {} {}'.format(author, author_time))
        lines.append('committer {} {}'.format(author, author_time))
        lines.append('')
        lines.append(message)
        lines.append('')
        data = '\n'.join(lines).encode()
        sha1 = hash_obj(data, 'commit')
        master_path = os.path.join('.git', 'refs', 'heads', 'master')
        write_file(master_path, (sha1 + '\n').encode())
        print('committed to master: {:7}'.format(sha1))
        return sha1