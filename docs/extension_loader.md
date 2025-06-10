# Extension Loader

The `disagreement.ext.loader` module provides simple helpers to manage optional
extensions. Extensions are regular Python modules that expose a `setup` function
called when the extension is loaded.

```python
from disagreement.ext import loader
```

- `loader.load_extension(name)` – Import and initialize an extension.
- `loader.unload_extension(name)` – Tear down and remove a previously loaded
  extension.
- `loader.reload_extension(name)` – Convenience wrapper that unloads then loads
  the extension again.
