# Convert the pool above to a safe RPC (remote procedure call)
# type operation.
import multiprocessing

WORKERS = 4


def say(msg):
    print(f'Saying: {msg}')


# Explicitly define the RPC methods to make this safer
RPC_METHODS = dict(say=say)


class RpcProcess(multiprocessing.Process):
    def __init__(self, queue: multiprocessing.Queue):
        super().__init__()
        self.queue = queue

    def run(self):
        while True:
            func_name, args, kwargs = self.queue.get()
            func = RPC_METHODS[func_name]
            func(*args, **kwargs)
            self.queue.task_done()


def main():
    q = multiprocessing.JoinableQueue()
    q.put(('say', ('hello',), {}))
    q.put(('say', ('world',), {}))
    # This should result in an error because this is not a valid
    # RPC method
    q.put(('non-existing-method', (), {}))

    for _ in range(WORKERS):
        p = RpcProcess(q)
        p.start()

    q.join()
    q.close()

    for p in multiprocessing.active_children():
        p.terminate()
        p.join()


if __name__ == '__main__':
    main()
