# Apply your functional programming skills and calculate
# something in a parallel way. Perhaps parallel sorting?
import multiprocessing
import random

# Since sorting is CPU limited we should not go above the number of
# CPU cores
WORKERS = multiprocessing.cpu_count()


def merge_sort(data):
    if len(data) <= 1:
        return data

    middle = len(data) // 2
    left = merge_sort(data[:middle])
    right = merge_sort(data[middle:])
    return merge(left, right)


def merge(left, right):
    '''
    Merge two sorted lists into one sorted list

    >>> merge([1, 3, 5], [2, 4, 6])
    [1, 2, 3, 4, 5, 6]
    >>> merge([1, 3, 5], [2, 4, 6, 7])
    [1, 2, 3, 4, 5, 6, 7]
    >>> merge([1, 2, 3], [1, 2, 3])
    [1, 1, 2, 2, 3, 3]
    '''
    result = []
    left_index = right_index = 0

    # When using iterators, we can avoid the IndexError of
    # accessing a non-existing element by using the `next`
    # function. This will raise a `StopIteration` error if
    # there are no more elements to iterate over.
    left_next = left[left_index]
    right_next = right[right_index]

    while True:
        try:
            if left_next <= right_next:
                result.append(left_next)
                left_index += 1
                left_next = left[left_index]
            else:
                result.append(right_next)
                right_index += 1
                right_next = right[right_index]
        except IndexError:
            # If we get an IndexError, it means that we have
            # reached the end of one of the lists. We can
            # simply extend the result with the remaining
            # elements and break out of the loop.
            result.extend(left[left_index:] or right[right_index:])
            break

    return result


def split(data, size=WORKERS):
    '''
    Split a list into `size` different chunks so that each chunk
    can be processed in parallel.
    '''
    chunk_size = len(data) // size
    return [data[i:i + chunk_size] for i in
            range(0, len(data), chunk_size)]


def multiprocessing_merge_sort(data):
    # Split the data into chunks
    with multiprocessing.Pool(processes=WORKERS) as pool:
        chunks = split(data, WORKERS)
        sorted_chunks = pool.map(merge_sort, chunks)

        # Merge the chunks
        i = 0
        while len(sorted_chunks) > 1:
            # zip the chunks into pairs
            pairs = zip(sorted_chunks[::2], sorted_chunks[1::2])
            # merge the pairs in parallel
            merged_chunks = pool.starmap(merge, pairs)

            # If we have an odd number of chunks, we need to
            # add the last chunk to the merged chunks
            if len(sorted_chunks) % 2 == 1:
                merged_chunks.append(sorted_chunks[-1])

            sorted_chunks = merged_chunks

    return sorted_chunks[0]


def main():
    data = random.sample(range(1000), 100)
    sorted_data = multiprocessing_merge_sort(data)
    # Verify that the data is sorted correctly
    assert sorted_data == sorted(data)


if __name__ == '__main__':
    main()
