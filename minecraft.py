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

_tag_names = ["TAG_End", "TAG_Byte", "TAG_Short", "TAG_Int",
              "TAG_Long", "TAG_Float", "TAG_Double", "TAG_Byte_Array",
              "TAG_String", "TAG_List", "TAG_Compound"]

_numeric_conversions = {
    TAG_BYTE: (">b", 1), TAG_SHORT: (">h", 2),
    TAG_INT: (">i", 4), TAG_LONG: (">q", 8),
    TAG_FLOAT: (">f", 4), TAG_DOUBLE: (">d", 8)}

def _parse_named_tag(file_):
    """Returns a named tag as a (value, type, name) tuple."""
    type_ = ord(file_.read(1))
    if type_ == TAG_END:
        # Early out because the other fields won't exist.
        return (None, type_, None)
    name = _parse_tag(TAG_STRING, file_)
    value = _parse_tag(type_, file_)
    return (value, type_, name)

def _write_named_tag(value, type_, name, file_):
    file_.write(chr(type_))
    _write_tag(name, TAG_STRING, file_)
    _write_tag(value, type_, file_)

def _parse_tag(tag_id, file_):
    """Helper to parse the actual data."""
    if tag_id == TAG_END:
        raise ValueError("Unexpected TAG_END")
    elif tag_id >= TAG_BYTE and tag_id <= TAG_DOUBLE:
        conversion = _numeric_conversions[tag_id]
        bytes = file_.read(conversion[1])
        return unpack(conversion[0], bytes)[0]
    elif tag_id == TAG_BYTE_ARRAY:
        length = _parse_tag(TAG_INT, file_)
        return file_.read(length)
    elif tag_id == TAG_STRING:
        length = _parse_tag(TAG_SHORT, file_)
        return file_.read(length).decode("UTF-8")
    elif tag_id == TAG_LIST:
        return NBTList.from_file(file_)
    elif tag_id == TAG_COMPOUND:
        return NBTCompound.from_file(file_)
    else:
        raise ValueError("Unknown tag type %d" % tag_id)

def _write_tag(value, tag_id, file_):
    """Helper to write the actual data."""
    if tag_id == TAG_END:
        raise ValueError("Unexpected TAG_END")
    elif tag_id >= TAG_BYTE and tag_id <= TAG_DOUBLE:
        conversion = _numeric_conversions[tag_id]
        file_.write(pack(conversion[0], value))
    elif tag_id == TAG_BYTE_ARRAY:
        _write_tag(len(value), TAG_INT, file_)
        file_.write(value)
    elif tag_id == TAG_STRING:
        string = value.encode("UTF-8")
        _write_tag(len(string), TAG_SHORT, file_)
        file_.write(string)
    elif tag_id == TAG_LIST:
        return NBTList.to_file(value, file_)
    elif tag_id == TAG_COMPOUND:
        return NBTCompound.to_file(value, file_)
    else:
        raise ValueError("Unknown tag type %d" % tag_id)

def _guess_type(value):
    """Tries to guess the tag type of a python data type."""
    if isinstance(value, int):
        return TAG_INT
    elif isinstance(value, long):
        return TAG_LONG
    elif isinstance(value, float):
        return TAG_DOUBLE
    elif isinstance(value, basestring):
        return TAG_STRING
    elif isinstance(value, NBTList):
        return TAG_LIST
    elif isinstance(value, NBTCompound):
        return TAG_COMPOUND
    else:
        raise ValueError("Can't figure out a type for %r", value)


class NBTCompound(dict):
    """Represents an NBT Compound object.

    Rather than having a class per tag type, we only wrap dicts (NBTCompound)
    and lists (NBTList), and use native python types for the leaf values.

    Every memeber has a type value that is used for serialization. If the type
    is not specified, one will be guessed based on the native python type:
    INT, LONG, DOUBLE, or STRING as appropriate.
    """

    def __init__(self, *args, **kwargs):
        super(NBTCompound, self).__init__(*args, **kwargs)
        self.types = {}

    @classmethod
    def from_file(cls, file_):
        nbt = NBTCompound()
        while True:
            value, tag_id, name = _parse_named_tag(file_)
            if tag_id == TAG_END:
                return nbt
            nbt[name] = value
            nbt.types[name] = tag_id

    def to_file(self, file_):
        for name, value in self.iteritems():
            type_ = self.types.setdefault(name, _guess_type(value))
            _write_named_tag(value, type_, name, file_)
        file_.write('\0')

class NBTFile(NBTCompound):
    """The top-level object that represents a parsed NBT file.

    This differs from NBTCompound only in that it has a name, and additional
    methods.
    """
    def __init__(self, *args, **kwargs):
        super(NBTFile, self).__init__(*args, **kwargs)
        self.name = ""

    @classmethod
    def from_file(cls, file_):
        """Returns a parsed Compound from a file-like object."""
        compound, type_, name = _parse_named_tag(file_)
        if type_ != TAG_COMPOUND:
            raise ValueError("Top-level tag of type %d, expected %d" %
                             (type_, TAG_COMPOUND))
        nbt = NBTFile(compound)
        nbt.name = name
        return nbt

    @classmethod
    def from_string(cls, string):
        """Returns a parsed Compound from a string."""
        return cls.from_file(StringIO(string))

    @classmethod
    def from_filename(cls, filename):
        """Returns a parsed Compound from a NBT file with the given filename."""
        return cls.from_file(GzipFile(filename))

    def to_file(self, file_):
        """Serialize this compound to a file-like stream."""
        _write_named_tag(self, TAG_COMPOUND, self.name, file_)

    def to_string(self):
        """Serialize this compound as a string."""
        io = StringIO()
        self.to_file(io)
        return io.getvalue()

    def to_filename(self, filename):
        """Serialize to an NBT file."""
        file_ = GzipFile(filename, "wb")
        self.to_file(file_)


class NBTList(list):
    """Represents an NBT List object.

    This is wrapped in a class because the type_ property specifies the type
    across all the items. If the type is unspecified it will be guessed during
    serialization based on the first member."""

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.type_ = None

    @classmethod
    def from_file(cls, file_):
        """Returns a parsed list from a file-like object."""

        list_ = NBTList()
        list_.type_ = _parse_tag(TAG_BYTE, file_)
        length = _parse_tag(TAG_INT, file_)
        for unused in range(length):
            list_.append(_parse_tag(list_.type_, file_))
        return list_

    def to_file(self, file_):
        """Serializes the list to a file-like object."""
        if self.type_ is None:
            if len(self):
                self.type_ = _guess_type(self[0])
            else:
                # Assume INT for lack of anything smarter.
                self.type_ = TAG_INT
        _write_tag(self.type_, TAG_BYTE, file_)
        _write_tag(len(self), TAG_INT, file_)
        for item in self:
            _write_tag(item, self.type_, file_)
