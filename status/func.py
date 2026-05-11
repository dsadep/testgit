from utils import get_status

class Status:
    def status():
        changed, new, deleted = get_status()
        if changed:
            print('changed files:')
            for path in changed: 
                print('   ', path)
        if new:
            print('new files:')
            for path in new:
                print('   ', path)
        if deleted:
            print('deleted files:')
            for path in deleted:
                print('   ', path)