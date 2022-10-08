import random


def quicksort(nums, left=None, right=None):
    if left is None:
        left = 0
    if right is None:
        right = len(nums) - 1
    if right <= left:
        return
    j = left
    temp = nums[right]
    for i in range(left, right):
        if nums[i] < temp:
            nums[i], nums[j] = nums[j], nums[i]
            j += 1
    nums[j], nums[right] = nums[right], nums[j]
    quicksort(nums, left, j - 1)
    quicksort(nums, j + 1, right)
    return nums


def main():
    nums = random.sample(range(100000), 100000)
    assert sorted(nums) == quicksort(nums)


if __name__ == '__main__':
    main()
