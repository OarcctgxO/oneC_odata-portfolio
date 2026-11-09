from typing import Literal

def accurate_sum(needed: int, nums: list[int], mode: Literal['exact', 'top', 'bot'] = 'exact')-> list[int]:
    """
    Находит подмножество nums, сумма которого равна needed. Только натуральные числа.
    В разных режимах возращает или только запрашиваемую сумму, или ближайшую сверху или снизу.

    Аргументы:
        needed (int): число, которое будет суммой подмножества;
        nums (list[int]): множество, из которого будет искаться подмножество;
        mode ('exact', 'top' или 'bot'): указание метода подбора
            exact - только точное попадание в needed;
            top - needed или ближайшая сверху достижимая сумма;
            bot - needed или ближайшая снизу достижимая сумма.

    Выводит:
        list[int]: искомое подмножество, сумма которого равна needed (или ближайшей в режиме сверху/снизу).
    """
    #проверка введенных данных
    if not nums:
        raise ValueError('Передан пустой список')
    for i in nums:
        if not (i > 0 and isinstance(i, int)):
            raise ValueError(f'Ненатуральное число в списке: {i}')
    if not (needed > 0 and isinstance(needed, int)):
        raise ValueError(f'Запрашиваемая сумма ненатуральна: {needed}')
    
    #сортировка
    nums.sort(reverse=True) #по убыванию
    
    total_sum = sum(nums)
    if needed == total_sum:
        return nums
    elif needed > total_sum:
        if mode == 'exact':
            raise ValueError('Запрашиваемая сумма несоставима этими элементами, needed > total_sum')
        else:
            return nums
   
    #массив достижимых сумм
    max_sum = needed
    if mode == 'top':
        max_sum += nums[0]
    
    dp = [-1] * (max_sum + 1)
    dp[0] = 0
    exit_flag = False
    
    #заполнение массива достижимых сумм
    for n in nums:
        for i in range(max_sum, n-1, -1):
            if dp[i-n] != -1 and dp[i] == -1:
                dp[i] = n
                if i == needed:
                    exit_flag = True
                    break
        if exit_flag:
            break
    
    #проверка достижимости
    if not exit_flag and mode == 'exact':
        raise ValueError('Запрашиваемая сумма несоставима этими элементами')
    else:
        possible_sum = needed
        while dp[possible_sum] == -1:
            if mode == 'top':
                possible_sum += 1
            else:
                possible_sum -= 1
    
    #восстановление использованных элементов
    current_sum = possible_sum
    final_list = []
    while current_sum:
        final_list.append(dp[current_sum])
        current_sum -= dp[current_sum]
    
    return final_list[::-1]
