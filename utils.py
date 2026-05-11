import collections
import enum
import hashlib
import os
import stat
import struct
import zlib

import urllib, urllib.request


class ObjectType(enum.Enum):
    commit = 1
    tree = 2
    blob = 3

IndexEntry = collections.namedtuple('IndexEntry', [
    'ctime_s', 'ctime_n', 'mtime_s', 'mtime_n', 'dev', 'ino', 'mode',
    'uid', 'gid', 'size', 'sha1', 'flags', 'path',
])

def read_file(path):
    with open(path, 'rb') as f:
        return f.read()

def write_file(path, data):
    with open(path, 'wb') as f:
        f.write(data)

def write_index(entries):
    packed_entries = []
    for entry in entries:
        entry_head = struct.pack('!LLLLLLLLLL20sH',
                entry.ctime_s, entry.ctime_n, entry.mtime_s, entry.mtime_n,
                entry.dev, entry.ino, entry.mode, entry.uid, entry.gid,
                entry.size, entry.sha1, entry.flags)
        path = entry.path.encode()
        length = ((62 + len(path) + 8) // 8) * 8
        packed_entry = entry_head + path + b'\x00' * (length - 62 - len(path))
        packed_entries.append(packed_entry)
    header = struct.pack('!4sLL', b'DIRC', 2, len(entries))
    all_data = header + b''.join(packed_entries)
    digest = hashlib.sha1(all_data).digest()
    write_file(os.path.join('.git', 'index'), all_data + digest)

def find_object(sha1_prefix):
    if len(sha1_prefix) < 2:
        raise ValueError
    obj_dir = os.path.join('.git', 'objects', sha1_prefix[:2])
    rest = sha1_prefix[2:]
    objects = [name for name in os.listdir(obj_dir) if name.startswith(rest)]
    if not objects: 
        raise ValueError('Objects {!r} not found'.format(sha1_prefix))
    if len(objects) >= 2:
        raise ValueError('multiple objects ({}) with prefix {!r}'.format(
            len(objects), sha1_prefix))
    return os.path.join(obj_dir, objects[0])

def read_object(sha1_prefix):
    path = find_object(sha1_prefix)
    full_data = zlib.decompress(read_file(path))
    nul_index = full_data.index(b'\x00')
    header = full_data[:nul_index]
    obj_type, size_str = header.decode().split()
    size = int(size_str)
    data = full_data[nul_index + 1:]
    assert len(data) == size, 'expected size {}, got {} bytes'.format(
        size, len(data))
    return (obj_type, data)

def read_tree(sha1=None, data=None):
    if sha1 is not None:
        obj_type, data = read_object(sha1)
        assert obj_type == 'tree'
    elif data is None:
        raise TypeError('must specify "sha1" or "data"')
    i = 0 
    entries = []
    for _ in range(1000):
        end = data.find(b'\x00', i)
        if end == -1:
            break
        mode_str, path = data[i:end].decode().split()
        mode = int(mode_str, 8)
        digest = data[end + 1:end + 21]
        entries.append(mode, path, digest.hex())
        i = end + 1 + 20
    return entries

def read_index():
    try:
        data = read_file(os.path.join('.git', 'index'))
    except FileNotFoundError:
        return []

    digest = hashlib.sha1(data[:-20]).digest()
    assert digest == data[-20:]

    signature, version, num_entries = struct.unpack('!4sLL', data[:12])
    assert signature == b'DIRC', \
        'invalid index signature {}'.format(signature)
    assert version == 2, 'unknown index version {}'.format(version)

    entry_data = data[12:-20]
    entries = []
    i = 0

    while i + 62 <= len(entry_data):
        fields_end = i + 62
        fields = struct.unpack('!LLLLLLLLLL20sH', entry_data[i:fields_end])

        path_end = entry_data.index(b'\x00', fields_end)
        path = entry_data[fields_end:path_end]
        entry = IndexEntry(*(fields + (path.decode('utf-8'),)))
        entries.append(entry)

        entry_len = ((62 + len(path) + 1 + 7) // 8) * 8
        i += entry_len

        if len(entries) == num_entries:
            break

    assert len(entries) == num_entries
    return entries



def get_status():
    paths = set()
    ignored_dirs = {'venv', '.git', '__pycache__'}

    for root, dirs, files in os.walk('.'):
        dirs_to_keep = []
        for d in dirs:
            dir_path = os.path.join(root, d).replace('\\', '/')
            if dir_path.startswith('./'):
                dir_path = dir_path[2:]

            if d in ignored_dirs:
                paths.add(dir_path + '/')
            else:
                dirs_to_keep.append(d)

        dirs[:] = dirs_to_keep

        for file in files:
            path = os.path.join(root, file).replace('\\', '/')
            if path.startswith('./'):
                path = path[2:]
            paths.add(path)

    entries_by_path = {e.path: e for e in read_index()}
    entry_paths = set(entries_by_path)
    changed = {p for p in (paths & entry_paths)
               if not p.endswith('/') and
               hash_obj(read_file(p), 'blob', write=False) !=
               entries_by_path[p].sha1.hex()}
    new = paths - entry_paths
    deleted = entry_paths - paths
    return (sorted(changed), sorted(new), sorted(deleted))

def write_tree():
    tree_entries = []
    for entry in read_index():
        # assert '/' not in entry.path, \
        #        'currently only supports a single, top-level directory'
        mode_path = '{:0} {}'.format(entry.mode, entry.path).encode()
        tree_entry = mode_path + b'\x00' + entry.sha1
        tree_entries.append(tree_entry)
    return hash_obj(b''.join(tree_entries), 'tree')

def get_local_master_hash():
    master_path = os.path.join('.git', 'refs', 'heads', 'master')
    try:
        
        return read_file(master_path).decode().strip()
    except FileNotFoundError:
        return None

def hash_obj(data, obj_type, write=True):
    header = '{} {}'.format(obj_type, len(data)).encode()
    full_data = header + b'\x00' + data
    sha1 = hashlib.sha1(full_data).hexdigest()
    if write:
        path = os.path.join('.git', 'objects', sha1[:2], sha1[2:])
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            write_file(path, zlib.compress(full_data))
    return sha1    

def extract_lines(data):
    lines = []
    i = 0
    for _ in range(1000):
        line_len = int(data[i:i+4], 16)
        line = data[i + 4:i + line_len]
        lines.append(line)
        if line_len == 0:
            i += 4
        else:
            i += line_len
        if i >= len(data):
            break
    return lines

def build_lines_data(lines):
    result = []
    for line in lines:
        result.append('{:04x}'.format(len(line) + 5).encode())
        result.append(line)
        result.append(b'\n')
    result.append(b'0000')
    return b''.join(result)

def http_request(url, username, password, data=None):
    password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password(None, url, username, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_manager)
    opener = urllib.request.build_opener(auth_handler)
    try:
        f = opener.open(url, data=data)
        return f.read()
    except urllib.error.HTTPError as e:
        raise e

def get_remote_master_hash(git_url, username, password):
    url = git_url + '/info/refs?service=git-receive-pack'
    responce = http_request(url, username, password)
    lines = extract_lines(responce)
    assert lines[0] == b'# service=git-receive-pack\n'
    assert lines[1] == b''
    if lines[2][:40] == b'0' * 40:
        return None
    master_sha1, master_ref = lines[2].split(b'\x00')[0].split()
    assert master_ref == b'refs/heads/main'
    assert len(master_sha1) == 40
    return master_sha1.decode()

def read_tree(sha1=None, data=None):
    """Read tree object with given SHA-1 (hex string) or data, and return list
    of (mode, path, sha1) tuples.
    """
    if sha1 is not None:
        obj_type, data = read_object(sha1)
        assert obj_type == 'tree'
    elif data is None:
        raise TypeError('must specify "sha1" or "data"')
    i = 0
    entries = []
    for _ in range(1000):
        end = data.find(b'\x00', i)
        if end == -1:
            break
        mode_str, path = data[i:end].decode().split()
        mode = int(mode_str, 8)
        digest = data[end + 1:end + 21]
        entries.append((mode, path, digest.hex()))
        i = end + 1 + 20
    return entries

def find_tree_objects(tree_sha1):
    objects = {tree_sha1}
    for mode, path, sha1 in read_tree(sha1=tree_sha1):
        if stat.S_ISDIR(mode):
            objects.update(find_tree_objects(sha1))
        else:
            objects.add(sha1)
    return objects

def find_commit_objects(commit_sha1):
    objects = {commit_sha1}
    obj_type, commit = read_object(commit_sha1)
    assert obj_type == 'commit'
    lines = commit.decode().splitlines()
    tree = next((l.split(' ', 1)[1] for l in lines if l.startswith('tree ')), None)
    print(tree)
    if tree is None:
        raise ValueError('bad commit {}: no tree line'.format(commit_sha1))
    objects.update(find_tree_objects(tree))
    parents = [l.split(' ', 1)[1] for l in lines if l.startswith('parent ')]
    print(parents)
    for parent in parents:
        objects.update(find_commit_objects(parent))
    return objects

def find_missing_objects(local_sha1, remote_sha1):
    local_obj = find_commit_objects(local_sha1)

    try:
        remote_obj = find_commit_objects(remote_sha1) if remote_sha1 is not None else set()
    except FileNotFoundError:
        remote_obj = set()
    
    return local_obj - remote_obj


def encode_pack_object(obj):
    obj_type, data = read_object(obj)
    type_num = ObjectType[obj_type].value
    size = len(data)
    byte = (type_num << 4) | (size & 0x0f)
    size >>= 4
    header = []
    while size:
        header.append(byte | 0x80)
        byte = size & 0x7f
        size >>= 7
    header.append(byte)
    return bytes(header) + zlib.compress(data)

def create_pack(objects):
    header = struct.pack('!4sLL', b'PACK', 2, len(objects))
    body = b''.join(encode_pack_object(o) for o in sorted(objects))
    contents = header + body
    sha1 = hashlib.sha1(contents).digest()
    return contents + sha1 

