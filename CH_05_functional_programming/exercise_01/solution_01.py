import random


def quicksort(nums, left=None, right=None):
    if right <= left:
        return
    j = left
    temp = nums[right]
    for i in range(left, right):
        if nums[i] < temp:
            nums[i], nums[j] = nums[j], nums[i]
            j += 1
    nums[j], nums[right] = nums[right], nums[j]
    quicksort(nums, left, j-1)
    quicksort(nums, j+1, right)
    return nums


if __name__ == '__main__':
    nums = [random.randint(1, 100000) for _ in range(10000)]
    assert sorted(nums) == quicksort(nums, 0, len(nums)-1)
