# See if you can make an echo server and client as separate
# processes. Even though we did not cover
# `multiprocessing.Pipe()`, I trust you can work with it
# regardless. It can be created through
# `a, b = multiprocessing.Pipe()` and you can use it with
# `a.send()` or `b.send()` and `a.recv()` or `b.recv()`.
import multiprocessing


def echo_client(receive_pipe, send_pipe, message):
    print('client sending', message)
    send_pipe.send(message)
    print('client received', receive_pipe.recv())


def echo_server(receive_pipe, send_pipe):
    while True:
        message = receive_pipe.recv()
        print('server received', message)
        send_pipe.send(message)


if __name__ == '__main__':
    a, b = multiprocessing.Pipe()
    server = multiprocessing.Process(
        target=echo_server,
        args=(a, b),
    )
    server.start()

    for i in range(5):
        client = multiprocessing.Process(
            target=echo_client,
            args=(a, b, f'message {i}'),
        )
        client.start()
        client.join()

    server.terminate()
    server.join()
