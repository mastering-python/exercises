from collections.abc import Callable

class SortedDict:
  def __init__(self, _dict: dict, keyfunc: Callable) -> None:
    self.unsorted = _dict
    self.keyfunc = keyfunc

    self._dict = self.sort()
    
  def sort(self) -> dict:
    sorted_list = sorted(self.unsorted.items(), key=self.keyfunc)
    sorted_dict = {k:v for k, v in sorted_list}
    return sorted_dict

  def __repr__(self):
    return repr(self._dict)
