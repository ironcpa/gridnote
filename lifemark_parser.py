

class Node:
    def __init__(self, indent, header, content):
        self.indent = int(indent)
        self.header = header
        self.content = content
        self.children = []
        self.parent = None

    def __item__(self, index):
        return self.children[index]

    def __repr__(self):
        return 'i={}, h={}: {}, p=<{}>'.format(self.indent,
                                               self.header,
                                               self.content,
                                               self.parent)

    def __iter__(self):
        return iter(self.children)

    def depth_first(self):
        yield self
        for c in self:
            yield from c.depth_first()

    def set_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)
        child.set_parent(self)


def split_spaces(text):
    spaces = ''
    last_i = 0
    for i, c in enumerate(text):
        last_i = i
        if c in (' ', '\t'):
            spaces += c
        else:
            break
    return spaces, text[last_i:]


def tokenize(text):
    indent, rest = split_spaces(text)
    header = rest[0]
    _, content = split_spaces(rest[1:])
    return indent, header, content


def parse2nodes(text):
    # how to ignore indent size
    #  - sometimes it's only 1
    #  - have to allow any length of sizes in single content
    indent_size = 2

    text = text.replace('\r', '')
    lines = text.split('\n')
    root = Node(0, '', 'root')
    prev = root

    for ln in lines:
        if len(ln) == 0:
            break

        depth, header, content = tokenize(ln)
        indent = len(depth) / indent_size
        if content != 'root':
            indent += 1

        node = Node(indent, header, content)

        indent_diff = node.indent - prev.indent
        if prev:
            if indent_diff == 1:
                prev.add_child(node)
            elif indent_diff == 0:
                prev.parent.add_child(node)
            elif indent_diff == -1:
                prev.parent.parent.add_child(node)
            elif indent_diff >= -2:
                root.add_child(node)

        prev = node
        print(node)

    return root
