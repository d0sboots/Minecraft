#!/usr/bin/python

from minecraft import NBTFile
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

if __name__ == '__main__':
    unittest.main()
