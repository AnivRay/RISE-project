import ast


def main():
    output = open("result.txt", "w+")
    pythonfile = open("scraperNPR.py", "r")
    node = ast.parse(pythonfile.read())
    analyzer = Analyzer(output)
    analyzer.dump(node)
    output.close()


class Analyzer(ast.NodeVisitor):
    output = file
    connectionMethods = set

    def __init__(self, f):
        self.output = f
        self.connectionMethods = {"Request", "urlopen", "build_opener", "open", "get", "getRequest"}

    def dump (self, node):
        self.output.write("token: " + ast.dump(node))

    def visit_Import(self, node):
        """for token in node.names:
            self.output.write("Imported: " + token.name + " \n")"""
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """for token in node.names:
            self.output.write("Imported From: " + token.name + " \n")"""
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.output.write("Class: " + node.name + "\n")
        self.generic_visit(node)

    def visit_Call(self, node, *args):
        isConnenctionMethod = False
        if isinstance(node.func, ast.Name):
            if node.func.id in self.connectionMethods:
                isConnenctionMethod = True
                self.output.write("Called: " + node.func.id + "( ")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.connectionMethods:
                isConnenctionMethod = True
                prefix = ""
                if isinstance(node.func.value, ast.Name):
                    prefix = node.func.value.id + "."
                self.output.write("Called: " + prefix + node.func.attr + "( ")
        if isConnenctionMethod:
            for argument in node.args:
                if isinstance(argument, ast.Name):
                    self.output.write(argument.id + " ")
                elif isinstance(argument, ast.Str):
                    self.output.write(argument.s + " ")
                elif isinstance(argument, ast.Call):
                    self.visit_Call(argument, True)
            for argument in node.keywords:
                self.output.write(argument.arg + " ")
            if not args:
                self.output.write(")\n")
        self.generic_visit(node)


main()
print "Finished"
