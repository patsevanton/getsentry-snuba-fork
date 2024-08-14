"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""

import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class AndFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FILTERS_FIELD_NUMBER: builtins.int
    @property
    def filters(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___TraceItemFilter]: ...
    def __init__(
        self,
        *,
        filters: collections.abc.Iterable[global___TraceItemFilter] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["filters", b"filters"]) -> None: ...

global___AndFilter = AndFilter

@typing.final
class OrFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FILTERS_FIELD_NUMBER: builtins.int
    @property
    def filters(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___TraceItemFilter]: ...
    def __init__(
        self,
        *,
        filters: collections.abc.Iterable[global___TraceItemFilter] | None = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["filters", b"filters"]) -> None: ...

global___OrFilter = OrFilter

@typing.final
class NumericalFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _Op:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _OpEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[NumericalFilter._Op.ValueType], builtins.type):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        LESS_THAN: NumericalFilter._Op.ValueType  # 0
        GREATER_THAN: NumericalFilter._Op.ValueType  # 1
        LESS_THAN_OR_EQUALS: NumericalFilter._Op.ValueType  # 2
        GREATER_THAN_OR_EQUALS: NumericalFilter._Op.ValueType  # 3
        EQUALS: NumericalFilter._Op.ValueType  # 4
        NOT_EQUALS: NumericalFilter._Op.ValueType  # 5

    class Op(_Op, metaclass=_OpEnumTypeWrapper): ...
    LESS_THAN: NumericalFilter.Op.ValueType  # 0
    GREATER_THAN: NumericalFilter.Op.ValueType  # 1
    LESS_THAN_OR_EQUALS: NumericalFilter.Op.ValueType  # 2
    GREATER_THAN_OR_EQUALS: NumericalFilter.Op.ValueType  # 3
    EQUALS: NumericalFilter.Op.ValueType  # 4
    NOT_EQUALS: NumericalFilter.Op.ValueType  # 5

    KEY_FIELD_NUMBER: builtins.int
    OP_FIELD_NUMBER: builtins.int
    VALUE_FIELD_NUMBER: builtins.int
    key: builtins.str
    op: global___NumericalFilter.Op.ValueType
    value: builtins.float
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        op: global___NumericalFilter.Op.ValueType = ...,
        value: builtins.float = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["key", b"key", "op", b"op", "value", b"value"]) -> None: ...

global___NumericalFilter = NumericalFilter

@typing.final
class StringFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _Op:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _OpEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[StringFilter._Op.ValueType], builtins.type):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        EQUALS: StringFilter._Op.ValueType  # 0
        NOT_EQUALS: StringFilter._Op.ValueType  # 1
        LIKE: StringFilter._Op.ValueType  # 2
        NOT_LIKE: StringFilter._Op.ValueType  # 3

    class Op(_Op, metaclass=_OpEnumTypeWrapper): ...
    EQUALS: StringFilter.Op.ValueType  # 0
    NOT_EQUALS: StringFilter.Op.ValueType  # 1
    LIKE: StringFilter.Op.ValueType  # 2
    NOT_LIKE: StringFilter.Op.ValueType  # 3

    KEY_FIELD_NUMBER: builtins.int
    OP_FIELD_NUMBER: builtins.int
    VALUE_FIELD_NUMBER: builtins.int
    key: builtins.str
    op: global___StringFilter.Op.ValueType
    value: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
        op: global___StringFilter.Op.ValueType = ...,
        value: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["key", b"key", "op", b"op", "value", b"value"]) -> None: ...

global___StringFilter = StringFilter

@typing.final
class ExistsFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    KEY_FIELD_NUMBER: builtins.int
    key: builtins.str
    def __init__(
        self,
        *,
        key: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing.Literal["key", b"key"]) -> None: ...

global___ExistsFilter = ExistsFilter

@typing.final
class TraceItemFilter(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    AND_FIELD_NUMBER: builtins.int
    OR_FIELD_NUMBER: builtins.int
    NUMBER_COMPARISON_FIELD_NUMBER: builtins.int
    STRING_COMPARISON_FIELD_NUMBER: builtins.int
    EXISTS_FIELD_NUMBER: builtins.int
    @property
    def number_comparison(self) -> global___NumericalFilter: ...
    @property
    def string_comparison(self) -> global___StringFilter: ...
    @property
    def exists(self) -> global___ExistsFilter: ...
    def __init__(
        self,
        *,
        number_comparison: global___NumericalFilter | None = ...,
        string_comparison: global___StringFilter | None = ...,
        exists: global___ExistsFilter | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing.Literal["and", b"and", "exists", b"exists", "number_comparison", b"number_comparison", "or", b"or", "string_comparison", b"string_comparison", "value", b"value"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing.Literal["and", b"and", "exists", b"exists", "number_comparison", b"number_comparison", "or", b"or", "string_comparison", b"string_comparison", "value", b"value"]) -> None: ...
    def WhichOneof(self, oneof_group: typing.Literal["value", b"value"]) -> typing.Literal["and", "or", "number_comparison", "string_comparison", "exists"] | None: ...

global___TraceItemFilter = TraceItemFilter