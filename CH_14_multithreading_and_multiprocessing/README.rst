Chapter 14 - multithreading and multiprocessing
=======================================================================================================================

1. See if you can make an echo server and client as separate processes. Even though we did not cover `multiprocessing.Pipe()`, I trust you can work with it regardless. It can be created through `a, b = multiprocessing.Pipe()` and you can use it with `a.send()` or `b.send()` and `a.recv()` or `b.recv()`.
2. Read all files in a directory and sum the size of the files by reading each file using `concurrent.futures`. If you want an extra challenge, walk through the directories recursively by letting the thread/process queue new items while running.
3. Read all files in a directory and sum the size of the files by reading each file using `threading` or `multiprocessing`
4. As above, but walk through the directories recursively by letting the thread/process queue new items while running.
5. Create a pool of workers that keeps waiting for items to be queued through `multiprocessing.Queue()`.
6. Convert the pool above to a safe RPC (remote procedure call) type operation.
7. Apply your functional programming skills and calculate something in a parallel way. Perhaps parallel sorting?
