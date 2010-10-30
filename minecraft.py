from struct import pack, unpack
from gzip import GzipFile
from cStringIO import StringIO

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

def _parse_named_tag(file_):
    """Returns a named tag as a (type, name, value) tuple."""
    type_ = ord(file_.read(1))
    name = _parse_tag(TAG_STRING, file_)
    value = _parse_tag(type_, file_)
    return (type_, name, value)

def _parse_tag(tag_id, file_):
    """Helper to parse the actual data."""
    if tag_id == TAG_END:
        raise ValueError("Unexpected TAG_END")
    elif tag_id >= TAG_BYTE and tag_id <= TAG_DOUBLE:
        return _parse_numeric(tag_id, file_)
    elif tag_id == TAG_BYTE_ARRAY:
        pass
    elif tag_id == TAG_STRING:
        pass
    elif tag_id == TAG_LIST:
        pass
    elif tag_id == TAG_COMPOUND:
        return _parse_compound(file_)
    else:
        raise ValueError("Unknown tag type %d" % type_)

_numeric_conversions = {
    }

def _parse_numeric(tag_id, file_):
    pass

def _parse_compound(file_):
    return NBT()

class NBT(dict):
    """Represents an NBT Compound object.

    Rather than having a class per tag type, we keep all the logic in the NBT
    class, and use native python types for the leaf values.
    """
    _tag_names = ["TAG_End", "TAG_Byte", "TAG_Short", "TAG_Int",
                  "TAG_Long", "TAG_Float", "TAG_Double", "TAG_Byte_Array",
                  "TAG_String", "TAG_List", "TAG_Compound"]
    @classmethod
    def from_file(cls, file_):
        """Returns a parsed NBT from a file-like object."""
        type_, name, nbt = _parse_named_tag(file_)
        if type_ != TAG_COMPOUND:
            raise ValueError("Top-level tag of type %d, expected %d" %
                             (type_, TAG_COMPOUND))
        nbt.name = name
        return nbt

    @classmethod
    def from_string(cls, string):
        """Returns a parsed NBT from a string."""
        return cls.from_file(StringIO(string))

    @classmethod
    def from_filename(cls, filename):
        """Returns a parsed NBT from a NBT file with the given filename."""
        return cls.from_file(GzipFile(filename))

    def to_file(self, file_):
        pass

    def to_string(self):
        io = StringIO()
        self.to_file(io)
        return io.getvalue()

    def to_filename(self, filename):
        file_ = GzipFile(filename, "wb")
        self.to_file(file_)
