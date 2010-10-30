#!/usr/bin/python

from minecraft import *
import unittest
from StringIO import StringIO
from gzip import GzipFile

class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.nbt = NBTFile.from_filename("bigtest.nbt")

    def testReadBig(self):
        # Test basic parsing works.
        self.assertEqual(self.nbt.name, "Level")
        self.assertEqual(self.nbt["byteTest"], 127)
        self.assertEqual(self.nbt.types["byteTest"], TAG_BYTE)

    def testWriteBig(self):
        output = self.nbt.to_string()
        newnbt = NBTFile.from_string(output)
        self.assertEqual(self.nbt, newnbt)

    def tearDown(self):
        pass


class EmptyStringTest(unittest.TestCase):
    def setUp(self):
        self.golden_value = "\x0A\0\x04Test\x08\0\x0Cempty string\0\0\0"
        self.nbt = NBTFile.from_string(self.golden_value)

    def testReadEmptyString(self):
        self.assertEqual(self.nbt.name, "Test")
        self.assertEqual(self.nbt["empty string"], "")

    def testWriteEmptyString(self):
        self.assertEqual(self.nbt.to_string(), self.golden_value)

    def tearDown(self):
        pass


class GuessTypesTest(unittest.TestCase):
    def setUp(self):
        pass

    def testCreateFromScratch(self):
        nbt = NBTFile()
        nbt.name = "Test"
        nbt["int"] = 5
        nbt["long"] = 5L
        nbt["double"] = 1.0
        nbt["string"] = "Hello World"
        nbt["list"] = NBTList([1, 2, 3])
        nbt["compound"] = NBTCompound()
        # Force guesstimation of types
        nbt.to_string()
        self.assertEqual(nbt.types["int"], TAG_INT)
        self.assertEqual(nbt.types["long"], TAG_LONG)
        self.assertEqual(nbt.types["double"], TAG_DOUBLE)
        self.assertEqual(nbt.types["string"], TAG_STRING)
        self.assertEqual(nbt.types["list"], TAG_LIST)
        self.assertEqual(nbt["list"].type_, TAG_INT)
        self.assertEqual(nbt, NBTFile.from_string(
            "\x0A\0\x04Test\x03\0\x03int\0\0\0\x05"
            "\x04\0\x04long\0\0\0\0\0\0\0\x05"
            "\x06\0\x06double?\xf0\0\0\0\0\0\0"
            "\x08\0\x06string\0\x0BHello World"
            "\x09\0\x04list\x03\0\0\0\x03\0\0\0\x01\0\0\0\x02\0\0\0\x03"
            "\x0A\0\x08compound\0\0"))

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
