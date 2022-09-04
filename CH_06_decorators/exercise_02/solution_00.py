# Extend the `track` function with min/max/average execution time and call 
# count.
import functools
import random
import time
from datetime import datetime, timedelta


def track(function=None, label=None):
    # Trick to add an optional argument to our decorator
    if label and not function:
        return functools.partial(track, label=label)

    execution_times = dict(
        min=timedelta.max,
        max=timedelta.min,
        total=timedelta(),
        count=0,
    )

    print(f'initializing {label}')

    @functools.wraps(function)
    def _track(*args, **kwargs):
        print(f'calling {label}')

        start = datetime.now()
        result = function(*args, **kwargs)
        end = datetime.now()

        duration = end - start
        execution_times['min'] = min(execution_times['min'], duration)
        execution_times['max'] = max(execution_times['max'], duration)
        execution_times['total'] += duration
        execution_times['count'] += 1

        print(f'called {label} in {duration}')
        return result

    def print_stats():
        print(f'{label} stats:')
        print(f'  min: {execution_times["min"]}')
        print(f'  max: {execution_times["max"]}')
        print(f'  total: {execution_times["total"]}')
        print(f'  avg: {execution_times["total"] / execution_times["count"]}')

    _track.print_stats = print_stats

    return _track


@track(label='random sleep')
def random_sleep():
    time.sleep(random.random())


if __name__ == '__main__':
    for i in range(10):
        random_sleep()

    random_sleep.print_stats()
