import asyncio


class DynamicSemaphore(asyncio.Semaphore):
    """
    Original: https://stepik.org/lesson/1580243/step/8?discussion=12232659&thread=solutions
    Мое решение задачи с динамическим семафором из курса на stepik.
    """
    def __init__(self, value: int):
        super().__init__(value)
        self._unreleases = 0
        self._max_value = value
    
    def set_width(self, new_value: int):

        if not isinstance(new_value, int) or new_value < 1:
            raise TypeError("Dynamic semaphore's width must be positive integer type.")
        elif new_value == self._max_value:
            return
        
        width_diff = new_value - self._max_value
        self._max_value = new_value
        if width_diff > 0:
            for _ in range(width_diff):
                self.release()
        elif width_diff < 0:
            self._unreleases += -width_diff
            while self._unreleases > 0 and self._value > 0:
                self._value -= 1
                self._unreleases -= 1
    

    def change_width(self, diff: int):
        self.set_width(self._max_value + diff)

        
    def release(self):
        if self._unreleases > 0:
            self._unreleases -= 1
        else:
            super().release()


    async def acquire(self):
        if self._max_value == 0:
            raise ValueError("Dynamic semaphore has shrinked to 0 width")
        return await super().acquire()