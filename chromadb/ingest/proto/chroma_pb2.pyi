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

class _ActionType:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ActionTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ActionType.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    INSERT: _ActionType.ValueType  # 0
    UPDATE: _ActionType.ValueType  # 1
    UPSERT: _ActionType.ValueType  # 2
    DELETE: _ActionType.ValueType  # 3

class ActionType(_ActionType, metaclass=_ActionTypeEnumTypeWrapper): ...

INSERT: ActionType.ValueType  # 0
UPDATE: ActionType.ValueType  # 1
UPSERT: ActionType.ValueType  # 2
DELETE: ActionType.ValueType  # 3
global___ActionType = ActionType

class _VectorEncoding:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _VectorEncodingEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_VectorEncoding.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    FLOAT32: _VectorEncoding.ValueType  # 0
    INT32: _VectorEncoding.ValueType  # 1

class VectorEncoding(_VectorEncoding, metaclass=_VectorEncodingEnumTypeWrapper): ...

FLOAT32: VectorEncoding.ValueType  # 0
INT32: VectorEncoding.ValueType  # 1
global___VectorEncoding = VectorEncoding

@typing_extensions.final
class Vector(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    DIMENSION_FIELD_NUMBER: builtins.int
    ENCODING_FIELD_NUMBER: builtins.int
    VECTOR_FIELD_NUMBER: builtins.int
    dimension: builtins.int
    encoding: global___VectorEncoding.ValueType
    vector: builtins.bytes
    def __init__(
        self,
        *,
        dimension: builtins.int = ...,
        encoding: global___VectorEncoding.ValueType = ...,
        vector: builtins.bytes = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["dimension", b"dimension", "encoding", b"encoding", "vector", b"vector"]) -> None: ...

global___Vector = Vector

@typing_extensions.final
class EmbeddingMessage(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    @typing_extensions.final
    class MetadataEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor

        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str = ...,
            value: builtins.str = ...,
        ) -> None: ...
        def ClearField(self, field_name: typing_extensions.Literal["key", b"key", "value", b"value"]) -> None: ...

    ID_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    VECTOR_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    id: builtins.str
    type: global___ActionType.ValueType
    @property
    def vector(self) -> global___Vector: ...
    @property
    def metadata(self) -> google.protobuf.internal.containers.ScalarMap[builtins.str, builtins.str]: ...
    def __init__(
        self,
        *,
        id: builtins.str = ...,
        type: global___ActionType.ValueType = ...,
        vector: global___Vector | None = ...,
        metadata: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["_vector", b"_vector", "vector", b"vector"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["_vector", b"_vector", "id", b"id", "metadata", b"metadata", "type", b"type", "vector", b"vector"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions.Literal["_vector", b"_vector"]) -> typing_extensions.Literal["vector"] | None: ...

global___EmbeddingMessage = EmbeddingMessage
