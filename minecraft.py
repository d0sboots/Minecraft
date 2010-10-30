from struct import pack, unpack

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10

class NBT(dict):
  """Represents an NBT Compound object.

  Rather than having a class per tag type, we keep all the logic in the
  NBT class, and use native python types for the leaf values.
  """
