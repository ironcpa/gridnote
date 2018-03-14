

class Node:
    def __init__(self, indent, header, content):
        self.indent = indent
        self.header = header
        self.content = content
        self.children = []
        self.parent = None

    def __item__(self, index):
        return self.children[index]

    def __repr__(self):
        return 'i={}, h={}: {}, p=<{}>'.format(len(self.indent),
                                               self.header,
                                               self.content,
                                               self.parent)

    def set_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)
        child.set_parent(self)


def split_spaces(text):
    spaces = ''
    for i, c in enumerate(text):
        if c in (' ', '\t'):
            spaces += c
        else:
            break
    return spaces, text[i:]


def tokenize(text):
    indent, rest = split_spaces(text)
    header = rest[0]
    _, content = split_spaces(rest[1:])
    return indent, header, content


def parse2nodes(text):
    lines = text.split('\n')
    root = Node('', '', 'root')
    prev = root

    for ln in lines:
        indent, header, content = tokenize(ln)
        depth = len(indent)

        node = Node(indent, header, content)

        if prev:
            if prev == root or node.indent > prev.indent:
                prev.add_child(node)
            elif node.indent == prev.indent:
                prev.parent.add_child(node)
            else:
                prev.parent.parent.add_child(node)

        prev = node
        print(node)

    return root
