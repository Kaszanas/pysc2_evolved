from __future__ import annotations

from google.protobuf.descriptor import FieldDescriptor


class MessageWrapper:
    """
    Wraps a dict to allow protobuf-style dot-notation attribute access.

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

    # Dict-like methods:
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

    def __setitem__(self, key, value):
        self._data[key] = value

    def __setattr__(self, name, value):
        self._data[name] = value

    def to_dict(self):
        """Return the raw underlying dict."""
        return self._data

    # Protobuf compatibility methods:
    def HasField(self, name):  # noqa: N802 – matches protobuf API
        """Return True if *name* is present and is not None."""
        return name in self._data and self._data[name] is not None

    def ListFields(self):  # noqa: N802
        """Yield (name, wrapped_value) pairs for every populated field."""
        return [(k, self._wrap(v)) for k, v in self._data.items() if v is not None]


class MessageWrapperDescriptorAware:
    """
    Wraps a dict to allow protobuf-style dot-notation attribute access.

    Nested dicts are recursively wrapped, so `obj.a.b.c` works when the
    underlying data is `{"a": {"b": {"c": value}}}`.

    Lists of dicts are returned as lists of MessageWrapper instances, enabling
    iteration with dot access on each element.

    Also provides protobuf-compatible `HasField` so existing proto-handling
    code can work transparently with dict data.

    If *proto_type* (a protobuf message **class**) is supplied, any attribute
    access for a field that is absent from the underlying dict will return the
    proto-defined default (0, "", False, [], or an empty nested wrapper).
    Nested dicts are automatically wrapped with the matching nested proto type.
    """

    __slots__ = ("_data", "_proto_type")

    def __init__(self, data: dict, proto_type=None):
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_proto_type", proto_type)

    # ---- proto introspection helpers --------------------------------

    def _field_descriptor(self, name):
        """Return the `FieldDescriptor` for *name*, or ``None``."""
        pt = self._proto_type
        if pt is None:
            return None
        desc = getattr(pt, "DESCRIPTOR", None)
        if desc is None:
            return None
        return desc.fields_by_name.get(name)

    def _nested_proto(self, name):
        """Return the proto class for a nested message field, or ``None``."""
        fd = self._field_descriptor(name)
        if fd is not None and fd.type == FieldDescriptor.TYPE_MESSAGE:
            return fd.message_type._concrete_class
        return None

    def _default_for_field(self, fd):
        """Return the proto-defined default for *fd*."""
        if fd.label == FieldDescriptor.LABEL_REPEATED:
            return []
        if fd.type == FieldDescriptor.TYPE_MESSAGE:
            return MessageWrapperDescriptorAware(
                {}, proto_type=fd.message_type._concrete_class
            )
        # Scalar: fd.default_value already gives 0 / "" / False / etc.
        return fd.default_value

    # ---- wrapping ------------------------------------------------------

    @staticmethod
    def _wrap_value(value, proto_type=None):
        """Wrap *value*, optionally propagating *proto_type* for dicts."""
        if isinstance(value, dict):
            return MessageWrapperDescriptorAware(value, proto_type=proto_type)
        if isinstance(value, list):
            return [
                MessageWrapperDescriptorAware._wrap_value(v, proto_type) for v in value
            ]
        return value

    def _wrap(self, value, field_name=None):
        """Wrap *value*, resolving the nested proto type from *field_name*."""
        return MessageWrapperDescriptorAware._wrap_value(
            value, self._nested_proto(field_name) if field_name else None
        )

    # ---- attribute / item access ---------------------------------------

    def __getattr__(self, name):
        try:
            return self._wrap(self._data[name], field_name=name)
        except KeyError:
            fd = self._field_descriptor(name)
            if fd is not None:
                return self._default_for_field(fd)
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
        if isinstance(other, MessageWrapperDescriptorAware):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    # Dict-like methods:
    def get(self, key, default=None):
        value = self._data.get(key, default)
        return self._wrap(value, field_name=key) if value is not default else default

    def keys(self):
        return self._data.keys()

    def values(self):
        return [self._wrap(v, field_name=k) for k, v in self._data.items()]

    def items(self):
        return [(k, self._wrap(v, field_name=k)) for k, v in self._data.items()]

    def __getitem__(self, key):
        return self._wrap(self._data[key], field_name=key)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __setattr__(self, name, value):
        self._data[name] = value

    def to_dict(self):
        """Return the raw underlying dict."""
        return self._data

    # Protobuf compatibility methods:
    def HasField(self, name):  # noqa: N802 – matches protobuf API
        """Return True if *name* is present and is not None."""
        return name in self._data and self._data[name] is not None

    def ListFields(self):  # noqa: N802
        """Yield (name, wrapped_value) pairs for every populated field."""
        return [
            (k, self._wrap(v, field_name=k))
            for k, v in self._data.items()
            if v is not None
        ]


if __name__ == "__main__":
    # Example usage:
    data = {
        "a": 1,
        "b": {"c": 2, "d": [3, {"e": 4}]},
        "f": None,
    }
    wrapper = MessageWrapper(data)
    print(wrapper.a)  # 1
    print(wrapper.b.c)  # 2
    print(wrapper.b.d[0])  # 3
    print(wrapper.b.d[1].e)  # 4
    print(wrapper.HasField("f"))  # False
    print(wrapper.HasField("a"))  # True
    print(
        wrapper.ListFields()
    )  # [('a', 1), ('b', MessageWrapper({'c': 2, 'd': [3, {'e': 4}]}))]

    wrapper.z = 5
    print(wrapper.z)  # 5
