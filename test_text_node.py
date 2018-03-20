from unittest import TestCase
from lifemark_parser import parse2nodes, tokenize


class TestTextNode(TestCase):
    def test_tokenize(self):
        text = " -   aaaa"
        indent, header, content = tokenize(text)
        self.assertEqual(indent, ' ')
        self.assertEqual(header, '-')
        self.assertEqual(content, 'aaaa')

        text = "  +   aaaa"
        indent, header, content = tokenize(text)
        self.assertEqual(indent, '  ')
        self.assertEqual(header, '+')
        self.assertEqual(content, 'aaaa')

    def test_parse_nodes(self):
        text = ("- aaaa\n"
                "  - bbbb\n"
                "  + cccc\n"
                "    + dddd\n"
                "  + eeee\n"
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
        self.assertEqual(root.children[1].header, '+')
        self.assertEqual(root.children[1].content, 'ffff')

    def test_parse_nodes_various_indents(self):
        text = ("- aaaa\n"
                "  - bbbb\n"
                "  > cccc\n"
                "    + dddd\n"
                "  p eeee\n"
                "+ ffff")

        root = parse2nodes(text)
        self.assertEqual(root.children[0].header, '-')
        self.assertEqual(root.children[0].content, 'aaaa')
        self.assertEqual(root.children[0].children[0].header, '-')
        self.assertEqual(root.children[0].children[0].content, 'bbbb')
        self.assertEqual(root.children[0].children[1].header, '>')
        self.assertEqual(root.children[0].children[1].content, 'cccc')
        self.assertEqual(root.children[0].children[1].children[0].header, '+')
        self.assertEqual(root.children[0].children[1].children[0].content, 'dddd')
        self.assertEqual(root.children[0].children[2].header, 'p')
        self.assertEqual(root.children[0].children[2].content, 'eeee')
        self.assertEqual(root.children[1].header, '+')
        self.assertEqual(root.children[1].content, 'ffff')

    def test_multi_root_children(self):
        text = ("- aaaa\r\n"
                "  - bbbb\r\n"
                "    - cccc\r\n"
                "+ dddd\r\n")

        root = parse2nodes(text)
        self.assertEqual(root.children[0].header, '-')
        self.assertEqual(root.children[0].content, 'aaaa')
        self.assertEqual(root.children[0].children[0].header, '-')
        self.assertEqual(root.children[0].children[0].content, 'bbbb')
        self.assertEqual(root.children[0].children[0].children[0].header, '-')
        self.assertEqual(root.children[0].children[0].children[0].content, 'cccc')
        self.assertEqual(root.children[1].header, '+')
        self.assertEqual(root.children[1].content, 'dddd')

    def test_parse_nodes_various_newline(self):
        text = ("- aaaa\r\n"
                "  - bbbb\r\n"
                "  > cccc\r\n"
                "    + dddd\r\n"
                "  p eeee\r\n"
                "    - dddd\r\n"
                "+ ffff")

        root = parse2nodes(text)
        self.assertEqual(root.children[0].header, '-')
        self.assertEqual(root.children[0].content, 'aaaa')
        self.assertEqual(root.children[0].children[0].header, '-')
        self.assertEqual(root.children[0].children[0].content, 'bbbb')
        self.assertEqual(root.children[0].children[1].header, '>')
        self.assertEqual(root.children[0].children[1].content, 'cccc')
        self.assertEqual(root.children[0].children[1].children[0].header, '+')
        self.assertEqual(root.children[0].children[1].children[0].content, 'dddd')
        self.assertEqual(root.children[0].children[2].header, 'p')
        self.assertEqual(root.children[0].children[2].content, 'eeee')
        self.assertEqual(root.children[0].children[2].children[0].header, '-')
        self.assertEqual(root.children[0].children[2].children[0].content, 'dddd')
        self.assertEqual(root.children[1].header, '+')
        self.assertEqual(root.children[1].content, 'ffff')

