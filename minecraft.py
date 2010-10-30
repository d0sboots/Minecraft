from struct import pack, unpack
from gzip import GzipFile
from cStringIO import StringIO
import os

##########################################################################
# NBT File Format helpers and classes
##########################################################################

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

# Internal helper methods for parsing and writing data
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
    """Helper to parse the actual data, given a tag type."""
    if tag_id == TAG_END:
        raise ValueError("Unexpected TAG_END")
    elif tag_id >= TAG_BYTE and tag_id <= TAG_DOUBLE:
        conversion = _numeric_conversions[tag_id]
        bytes = file_.read(conversion[1])
        value = unpack(conversion[0], bytes)[0]
        if tag_id == TAG_LONG:
            value = long(value)
        return value
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
    """Helper to write the actual data, given a tag type."""
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

def _format_value(type_, value, indent):
    if type_ == TAG_COMPOUND or type_ == TAG_LIST:
        string = value.pretty_string(indent + 3)
    elif type_ == TAG_BYTE_ARRAY:
        string = "[%d bytes]" % len(value)
    else:
        string = unicode(value)
    return string

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
        if len(args) and isinstance(args[0], NBTCompound):
            self.types = args[0].types
        else:
            self.types = {}

    @classmethod
    def from_file(cls, file_):
        """Parse a Compound from a file-like object."""
        nbt = NBTCompound()
        while True:
            value, tag_id, name = _parse_named_tag(file_)
            if tag_id == TAG_END:
                return nbt
            nbt[name] = value
            nbt.types[name] = tag_id

    def to_file(self, file_):
        """Serialize a Compound to a file-like object."""
        for name, value in self.iteritems():
            type_ = self.types.setdefault(name, _guess_type(value))
            _write_named_tag(value, type_, name, file_)
        file_.write('\0')

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def pretty_string(self, indent=0):
        """Output object in pretty tree form, like the example in the spec."""
        output = ["%d entries" % len(self), " " * indent + "{"]
        for name, value in self.iteritems():
            type_ = self.types.setdefault(name, _guess_type(value))
            output.append('%s%s("%s"): %s' % (
                " " * (indent + 3), _tag_names[type_], name,
                _format_value(type_, value, indent)))
        output.append(" " * indent + "}")
        return "\n".join(output)

class NBTFile(NBTCompound):
    """The top-level object that represents a parsed NBT file.

    This differs from NBTCompound only in that it has a name, and additional
    convenience methods.
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

    def pretty_string(self, indent=0):
        """Output object in pretty tree form, like the example in the spec."""
        return '%s("%s"): %s' % (_tag_names[TAG_COMPOUND], self.name,
                                 NBTCompound.pretty_string(self, indent))

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
        type_ = self.get_type()
        _write_tag(type_, TAG_BYTE, file_)
        _write_tag(len(self), TAG_INT, file_)
        for item in self:
            _write_tag(item, type_, file_)

    def get_type(self):
        """Get the type of this list.

        If the type was not set, it guesses based on the contents of the list
        right now.
        """
        if self.type_ is None:
            if len(self):
                self.type_ = _guess_type(self[0])
            else:
                # Assume INT for lack of anything smarter.
                self.type_ = TAG_INT
        return self.type_

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, list.__repr__(self))

    def pretty_string(self, indent=0):
        """Output object in pretty tree form, like the example in the spec."""
        type_ = self.get_type()
        output = ["%d entries of type %s" %
                    (len(self), _tag_names[type_]),
                  " " * indent + "{"]
        for value in self:
            output.append('%s%s: %s' % (" " * (indent + 3), _tag_names[type_],
                                         _format_value(type_, value, indent)))
        output.append(" " * indent + "}")
        return "\n".join(output)

##########################################################################
# Minecraft utility helpers and classes
##########################################################################

def base36(num):
    digits = []
    negative = False
    if num < 0:
        num = -num
        negative = True
    while num:
        value = num % 36
        if value < 10:
            digits.append(chr(48 + value))
        else:
            digits.append(chr(87 + value))
        num //= 36
    if negative:
        digits.append('-')
    digits.reverse()
    return ''.join(digits) or '0'

class Level(object):
    """A level is the root of all Minecraft Alpha level data.

    Although it's possible to create the world data from scratch, currently
    this clas requires a valid path to the world data to initialize. You can
    write out data to a different location by changing the path before calling
    write methods.

    This class does not use the session.lock file, so be careful if Minecraft
    is running concurrently on the same data!
    """

    def __init__(self, path):
        """Initialize given a path to the save data.

        Path usually looks like ".../.minecraft/saves/World1"
        """
        self.path = path
        self.data = NBTFile.from_filename(self._leveldat_filename())

    def leveldat_filename(self):
        return os.path.join(self.path, "level.dat")

    def path_to_chunk(self, x, z):
        pass
