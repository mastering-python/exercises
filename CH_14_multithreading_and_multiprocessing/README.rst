Chapter 14 - multithreading and multiprocessing
=======================================================================================================================

1. `See if you can make an echo server and client as separate processes. Even though we did not cover ``multiprocessing.Pipe()``, I trust you can work with it regardless. It can be created through ``a, b = multiprocessing.Pipe()`` and you can use it with ``a.send()`` or ``b.send()`` and ``a.recv()`` or ``b.recv()``. <exercise_01/>`_
2. `Read all files in a directory and sum the size of the files by reading each file using ``concurrent.futures``. If you want an extra challenge, walk through the directories recursively by letting the thread/process queue new items while running. <exercise_02/>`_
3. `Read all files in a directory and sum the size of the files by reading each file using ``threading`` and ``multiprocessing``. <exercise_03/>`_
4. `As above, walk through the directories recursively by letting the thread/process queue new items while running. <exercise_04/>`_
5. `Create a pool of workers that keeps waiting for items to be queued through ``multiprocessing.Queue()``. <exercise_05/>`_
6. `Convert the pool above into a safe RPC (remote procedure call) type of operation. <exercise_06/>`_
7. `Apply your functional skills to calculate something in a parallel way. Perhaps parallel sorting? <exercise_07/>`_
