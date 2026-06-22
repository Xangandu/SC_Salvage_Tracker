DEBUG = False


def debug_log(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
