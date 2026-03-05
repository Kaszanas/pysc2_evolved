class MessageWrapper:
    """Wraps a dict to allow protobuf-style dot-notation attribute access.

    Nested dicts are recursively wrapped, so `obj.a.b.c` works when the
    underlying data is `{"a": {"b": {"c": value}}}`.

    Lists of dicts are returned as lists of MessageWrapper instances, enabling
    iteration with dot access on each element.

    Also provides protobuf-compatible `HasField` so existing proto-handling
    code can work transparently with dict data.
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        object.__setattr__(self, "_data", data)

    @staticmethod
    def _wrap(value):
        """Wrap a value: dicts become MessageWrappers, lists are mapped."""
        if isinstance(value, dict):
            return MessageWrapper(value)
        if isinstance(value, list):
            return [MessageWrapper._wrap(v) for v in value]
        return value

    def __getattr__(self, name):
        try:
            return self._wrap(self._data[name])
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__!r} has no attribute {name!r} "
                f"(available keys: {list(self._data)})"
            ) from None

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __bool__(self):
        return bool(self._data)

    def __repr__(self):
        return f"{type(self).__name__}({self._data!r})"

    def __eq__(self, other):
        if isinstance(other, MessageWrapper):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    # --- dict-like helpers ---------------------------------------------------
    def get(self, key, default=None):
        value = self._data.get(key, default)
        return self._wrap(value) if value is not default else default

    def keys(self):
        return self._data.keys()

    def values(self):
        return [self._wrap(v) for v in self._data.values()]

    def items(self):
        return [(k, self._wrap(v)) for k, v in self._data.items()]

    def __getitem__(self, key):
        return self._wrap(self._data[key])

    # --- protobuf compatibility ----------------------------------------------
    def HasField(self, name):  # noqa: N802 – matches protobuf API
        """Return True if *name* is present and is not None."""
        return name in self._data and self._data[name] is not None

    def ListFields(self):  # noqa: N802
        """Yield (name, wrapped_value) pairs for every populated field."""
        return [(k, self._wrap(v)) for k, v in self._data.items() if v is not None]
