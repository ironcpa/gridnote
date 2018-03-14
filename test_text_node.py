from unittest import TestCase
from lifemark_parser import Node, parse2nodes, tokenize


class TestTextNode(TestCase):
    def test_tokenize(self):
        text = " -   aaaa"
        indent, header, content = tokenize(text)
        self.assertEqual(indent, ' ')
        self.assertEqual(header, '-')
        self.assertEqual(content, 'aaaa')

        text = "  +   aaaa"
        tokens = text.split()
        indent, header, content = tokenize(text)
        self.assertEqual(indent, '  ')
        self.assertEqual(header, '+')
        self.assertEqual(content, 'aaaa')

    def test_parse_nodes(self):
        text = ("- aaaa\n"
                " - bbbb\n"
                " + cccc\n"
                "  + dddd\n"
                " + eeee\n"
                "+ ffff")

        root = parse2nodes(text)
        self.assertEqual(root.children[0].header, '-')
        self.assertEqual(root.children[0].content, 'aaaa')
        self.assertEqual(root.children[0].children[0].header, '-')
        self.assertEqual(root.children[0].children[0].content, 'bbbb')
        self.assertEqual(root.children[0].children[1].header, '+')
        self.assertEqual(root.children[0].children[1].content, 'cccc')
        self.assertEqual(root.children[0].children[1].children[0].header, '+')
        self.assertEqual(root.children[0].children[1].children[0].content, 'dddd')
        self.assertEqual(root.children[0].children[2].header, '+')
        self.assertEqual(root.children[0].children[2].content, 'eeee')
        self.assertEqual(root.children[0].children[2].header, '+')
        self.assertEqual(root.children[0].children[2].content, 'eeee')
        self.assertEqual(root.children[1].header, '+')
        self.assertEqual(root.children[1].content, 'ffff')

