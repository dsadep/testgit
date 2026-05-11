import operator
import os

from utils import IndexEntry, hash_obj, read_file, read_index, write_index

class Add:
    def add(paths):
        paths = [p.replace('\\', '/') for p in paths]
        all_entries = read_index()
        entries = [e for e in all_entries if e.path not in paths]
        for path in paths:
            sha1 = hash_obj(read_file(path), 'blob')
            st = os.stat(path)
            flags = len(path.encode())
            assert flags < (1 << 12)
            entry = IndexEntry(
                    int(st.st_ctime), 0, int(st.st_mtime), 0, st.st_dev,
                    st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_size,
                    bytes.fromhex(sha1), flags, path)
            entries.append(entry)
        entries.sort(key=operator.attrgetter('path'))
        write_index(entries)