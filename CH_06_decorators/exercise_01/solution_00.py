# Extend the `track` function to monitor execution time.
import functools
import time
from datetime import datetime


def track(function=None, label=None):
    # Trick to add an optional argument to our decorator
    if label and not function:
        return functools.partial(track, label=label)

    print(f'initializing {label}')

    @functools.wraps(function)
    def _track(*args, **kwargs):
        print(f'calling {label}')

        start = datetime.now()
        result = function(*args, **kwargs)
        end = datetime.now()

        print(f'called {label} in {end - start}')

        return result

    return _track


@track(label='outer')
@track(label='inner')
def func():
    print('func')


@track(label='Slow function')
def slower_func():
    print('slower_func')
    time.sleep(0.5)


if __name__ == '__main__':
    func()
    slower_func()
