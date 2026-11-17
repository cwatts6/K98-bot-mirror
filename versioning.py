# versioning.py
def versioned(version):
    def decorator(func):
        func.__version__ = version
        return func

    return decorator
