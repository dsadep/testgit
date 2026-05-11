import os

from utils import build_lines_data, create_pack, extract_lines, find_missing_objects, get_local_master_hash, get_remote_master_hash, http_request


class Push:
    def push(git_url, username=None, password=None):
        if username is None:
            username = os.getenv('GIT_USERNAME')
        if password is None:
            password = os.getenv('GIT_PASSWORD')
        remote_sha1 = get_remote_master_hash(git_url, username, password)
        local_sha1 = get_local_master_hash()
        missing = find_missing_objects(local_sha1, remote_sha1)
        print(len(missing))
        print(missing)
        print('updating remote master from {} to {} ({} object{})'.format(
                remote_sha1 or 'no commits', local_sha1, len(missing),
                '' if len(missing) == 1 else 's'))
        lines = ['{} {} refs/heads/main\x00 report-status'.format(
                remote_sha1 or ('0' * 40), local_sha1).encode()]
        data = build_lines_data(lines) + create_pack(missing)
        url = git_url + '/git-receive-pack'
        response = http_request(url, username, password, data=data)
        lines = extract_lines(response)
        assert len(lines) >= 2, \
            'expected at least 2 lines, got {}'.format(len(lines))
        assert lines[0] == b'unpack ok\n', \
            "expected line 1 b'unpack ok', got: {}".format(lines[0])
        print(lines[1])
        assert lines[1] == b'ok refs/heads/main\n', \
            "expected line 2 b'ok refs/heads/master\n', got: {}".format(lines[1])
        return (remote_sha1, missing)