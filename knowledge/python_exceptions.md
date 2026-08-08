# Common Built-in Python Exceptions
Source: https://docs.python.org/3/library/exceptions.html

## SyntaxError
Raised when the parser encounters invalid Python syntax. Occurs during code
compilation (import, compile(), eval(), or reading a script).
```python
if x = 5:  # SyntaxError: invalid syntax (should be ==)
    pass
```

## IndentationError
A subclass of SyntaxError raised when indentation is incorrect.
```python
if True:
print("indented wrong")  # IndentationError: expected an indented block
```

## TabError
A subclass of IndentationError raised when indentation mixes tabs and spaces
inconsistently.
```python
if True:
	x = 1  # tab
    y = 2  # spaces - TabError: inconsistent use of tabs and spaces
```

## NameError
Raised when a local or global name is referenced but hasn't been defined.
```python
print(undefined_variable)  # NameError: name 'undefined_variable' is not defined
```

## TypeError
Raised when an operation or function is applied to an object of an
inappropriate type.
```python
len(5)  # TypeError: object of type 'int' has no len()
"hello" + 5  # TypeError: can only concatenate str (not "int") to str
```

## ValueError
Raised when an operation receives an argument of the correct type but an
inappropriate value.
```python
int("not_a_number")  # ValueError: invalid literal for int() with base 10
```

## KeyError
Raised when a dictionary key is not found.
```python
my_dict = {"a": 1}
print(my_dict["b"])  # KeyError: 'b'
```

## IndexError
Raised when a sequence subscript (index) is out of range.
```python
my_list = [1, 2, 3]
print(my_list[10])  # IndexError: list index out of range
```

## AttributeError
Raised when an attribute reference or assignment fails - accessing a
nonexistent attribute on an object.
```python
class MyClass:
    pass

obj = MyClass()
print(obj.nonexistent)  # AttributeError: 'MyClass' object has no attribute 'nonexistent'
```

## ZeroDivisionError
Raised when the second argument of a division or modulo operation is zero.
```python
result = 10 / 0  # ZeroDivisionError: division by zero
```

## ImportError & ModuleNotFoundError
ImportError is raised when an import statement fails to load a module.
ModuleNotFoundError is a subclass raised when a module cannot be located.
```python
import nonexistent_module  # ModuleNotFoundError: No module named 'nonexistent_module'
from os import nonexistent_function  # ImportError: cannot import name 'nonexistent_function'
```

## FileNotFoundError
A subclass of OSError raised when a file or directory is requested but
doesn't exist.
```python
with open("nonexistent_file.txt") as f:  # FileNotFoundError: [Errno 2] No such file or directory
    pass
```

## RecursionError
A subclass of RuntimeError raised when the interpreter detects the maximum
recursion depth has been exceeded.
```python
def infinite_recursion():
    return infinite_recursion()

infinite_recursion()  # RecursionError: maximum recursion depth exceeded
```

## StopIteration
Raised by next() and an iterator's __next__() method to signal there are no
more items to produce.
```python
my_iter = iter([1, 2])
next(my_iter)  # 1
next(my_iter)  # 2
next(my_iter)  # StopIteration
```

## OverflowError
Raised when the result of an arithmetic operation is too large to be
represented.
```python
import math
math.exp(1000)  # OverflowError: math range error
```

## PermissionError
A subclass of OSError raised when attempting an operation without adequate
access rights.
```python
open("/root/protected_file.txt", "r")  # PermissionError: [Errno 13] Permission denied
```
