# • Create a single-dispatch decorator that considers all or a configurable number of arguments
#   instead of only the first one.
from collections.abc import Iterable

class MiSingleDispatch:
    """Implementation type functools.singledispatch"""

    def __init__(self, func):
        self.default = func
        self.registry = {}
        self.registry[object] = func

    def register(self, *type_):
        """Registry function for type"""
        def decorator(impl_func):
            self.registry[type_] = impl_func
            return impl_func
        return decorator

    def __call__(self, *args, **kwargs):
        """Call the corresponding function"""
        if not args:
            return self.default(*args, **kwargs)

        arg_type = tuple()
        for arg in args:
            arg_type += (type(arg),)

        # 1. Exact search
        if arg_type in self.registry:
            return self.registry[arg_type](*args, **kwargs)

        # 2. Search by inheritance
        for type_key, impl in self.registry.items():
            if type_key is Iterable and all(isinstance(arg, tk) for arg, tk in zip(args, type_key))\
               and len(args) == len(type_key):
                return impl(*args, **kwargs)

        # 3. Default
        return self.default(*args, **kwargs)

@MiSingleDispatch
def procesar(*arg):
    return f"Default: {arg}"

@procesar.register(int)
def _(*arg):
    return f"One integer: {arg}"

@procesar.register(int, int)
def _(*arg):
    return f"Two integers: {arg}"

@procesar.register(str, str)
def _(*arg):
    return f"Two strings: {arg}"

@procesar.register(str, str, int)
def _(*arg):
    return f"Two strings and one integer: {arg}"

@procesar.register(int, int, str)
def _(*arg):
    return f"Two integers and one string: {arg}"

@procesar.register(list)
def _(*arg):
    return f"One list: {arg}"

@procesar.register(tuple)
def _(*arg):
    return f"One tuple: {arg}"

@procesar.register(dict)
def _(*arg):
    return f"One dict: {arg}"

print(procesar(42))
print(procesar(42,52))
print(procesar(42,52, "test"))
print(procesar("This", "is"))
print(procesar("Five", "is", 5))
print(procesar("This", "is", "one", "example"))
print(procesar())
print(procesar([1, 2, 3]))
print(procesar((1, 2, 3)))
print(procesar({1: "one", 2: "two", 3: "three"}))
