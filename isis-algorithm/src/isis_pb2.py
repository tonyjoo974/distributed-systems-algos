# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: isis.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='isis.proto',
  package='tutorial',
  syntax='proto2',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nisis.proto\x12\x08tutorial\"\xbc\x01\n\x04isis\x12\x19\n\x11proposed_sequence\x18\x01 \x02(\x05\x12$\n\x1cproposed_sequence_process_id\x18\x02 \x02(\t\x12 \n\x18message_owner_process_id\x18\x03 \x02(\t\x12\x19\n\x11sender_process_id\x18\x04 \x02(\t\x12\x12\n\nmessage_id\x18\x05 \x02(\t\x12\x0f\n\x07message\x18\x06 \x02(\t\x12\x11\n\tis_agreed\x18\x07 \x02(\x08'
)




_ISIS = _descriptor.Descriptor(
  name='isis',
  full_name='tutorial.isis',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='proposed_sequence', full_name='tutorial.isis.proposed_sequence', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='proposed_sequence_process_id', full_name='tutorial.isis.proposed_sequence_process_id', index=1,
      number=2, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message_owner_process_id', full_name='tutorial.isis.message_owner_process_id', index=2,
      number=3, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='sender_process_id', full_name='tutorial.isis.sender_process_id', index=3,
      number=4, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message_id', full_name='tutorial.isis.message_id', index=4,
      number=5, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message', full_name='tutorial.isis.message', index=5,
      number=6, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='is_agreed', full_name='tutorial.isis.is_agreed', index=6,
      number=7, type=8, cpp_type=7, label=2,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=25,
  serialized_end=213,
)

DESCRIPTOR.message_types_by_name['isis'] = _ISIS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

isis = _reflection.GeneratedProtocolMessageType('isis', (_message.Message,), {
  'DESCRIPTOR' : _ISIS,
  '__module__' : 'isis_pb2'
  # @@protoc_insertion_point(class_scope:tutorial.isis)
  })
_sym_db.RegisterMessage(isis)


# @@protoc_insertion_point(module_scope)
