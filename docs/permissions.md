# Permission Helpers

The `disagreement.permissions` module defines an :class:`~enum.IntFlag`
`Permissions` enumeration along with helper functions for working with
the Discord permission bitmask.

## Permissions Enum

Each attribute of ``Permissions`` represents a single permission bit. The value
is a power of two so multiple permissions can be combined using bitwise OR.

```python
from disagreement.permissions import Permissions

value = Permissions.SEND_MESSAGES | Permissions.MANAGE_MESSAGES
```

## Helper Functions

### ``permissions_value``

```python
permissions_value(*perms) -> int
```

Return an integer bitmask from one or more ``Permissions`` values. Nested
iterables are flattened automatically.

### ``has_permissions``

```python
has_permissions(current, *perms) -> bool
```

Return ``True`` if ``current`` (an ``int`` or ``Permissions``) contains all of
the provided permissions.

### ``missing_permissions``

```python
missing_permissions(current, *perms) -> List[Permissions]
```

Return a list of permissions that ``current`` does not contain.

## Example

```python
from disagreement.permissions import (
    Permissions,
    has_permissions,
    missing_permissions,
)

current = Permissions.SEND_MESSAGES | Permissions.MANAGE_MESSAGES

if has_permissions(current, Permissions.SEND_MESSAGES):
    print("Can send messages")

print(missing_permissions(current, Permissions.ADMINISTRATOR))
```

