import difflib

from utils import get_status, read_file, read_index, read_object

class Diff:
    def diff():
        changed, _, _ = get_status()
        entries_by_path = {e.path: e for e in read_index()}
        for i, path in enumerate(changed):
            sha1 = entries_by_path[path].sha1.hex()
            obj_type, data = read_object(sha1)
            assert obj_type == 'blob'
            index_lines = data.decode().splitlines()
            working_lines = read_file(path).decode().splitlines() 

            diff_lines = difflib.unified_diff(
                    index_lines, working_lines,
                    '{} (index)'.format(path),
                    '{} (working copy)'.format(path),
                    lineterm=''
            )
            for line in diff_lines:
                print(line)
            if i < len(changed) - 1:
                print('-' * 70)