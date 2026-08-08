# Essential PEP 8 Style Rules
Source: https://peps.python.org/pep-0008/

## Naming Conventions

Variables & functions: lowercase with underscores.
```python
user_name = "Alice"
def calculate_total():
    pass
```

Classes: CapWords (CamelCase).
```python
class DataProcessor:
    pass
```

Constants: all uppercase with underscores.
```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

## Indentation & Line Length

Use 4 spaces per indentation level. Never mix tabs and spaces. Keep lines to
79 characters maximum; docstrings/comments to 72.
```python
result = some_function(arg1, arg2,
                       arg3, arg4)
```

## Whitespace Around Operators

Surround binary operators with single spaces.
```python
x = y + 1
if x == 5 and y != 10:
    pass
```

## Blank Lines

Surround top-level function and class definitions with two blank lines. One
blank line between methods inside a class.

## Import Ordering

Group imports: standard library, then third-party, then local modules -
each group separated by a blank line.
```python
import os
import sys

import numpy as np

from myapp import utils
```

## Comparing to None & Booleans

Compare to None with `is`/`is not`, never `==`/`!=`.
```python
if x is None:
    pass
```

Don't compare booleans with `==`.
```python
if is_active:      # correct
    pass
if is_active == True:  # wrong
    pass
```
