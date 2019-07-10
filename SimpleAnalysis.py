import os
import ast


def main():
    for (dirname, dirs, files) in os.walk("C:\\Users\\anivr\\OneDrive\\Desktop\\Kodi Add-Ons\\AutoDownload2"):
        for filename in files:
            if filename.endswith(".py"):
                checker = ConnectionChecker()
                if checker.check_for_connection(dirname + "\\" + filename):
                    analyzer = Analyzer(open(dirname + "\\result.txt", "a+"))
                    analyzer.analyze(dirname + "\\" + filename)
    """finder = VariableFinder()
    # finder.findVariable("url", ast.parse(open("defaultYahoo.py", "r").read()))
    analyzer = Analyzer(open("result.txt", "w+"))
    analyzer.analyze("defaultYahoo.py")"""

class Analyzer(ast.NodeVisitor):
    output = file
    connectionMethods = set
    connectionClasses = set
    tempMethods = set

    def __init__(self, out):
        self.output = out
        self.connectionMethods = {"Request", "urlopen", "build_opener", "open", "get", "getRequest", "Session"}
        self.connectionClasses = {"self", "urllib", "urllib2", "requests", "httplib", "t1mlib"}
        self.tempMethods = {}

    def analyze(self, filename):
        pythonfile = open(filename, "r")
        self.output.write("Analyzing " + filename + "\n")
        node = ast.parse(pythonfile.read())
        self.visit(node)
        self.output.write("\n")
        self.output.close

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
            prefix = ""
            hasRightPrefix = True
            if isinstance(node.func.value, ast.Name):
                prefix = node.func.value.id
                if prefix not in self.connectionClasses:
                    hasRightPrefix = False
            if node.func.attr in self.connectionMethods and hasRightPrefix:
                isConnenctionMethod = True
                self.output.write("Called: " + prefix + "." + node.func.attr + "( ")
        if isConnenctionMethod:
            for argument in node.args:
                if isinstance(argument, ast.BinOp):
                    argument = argument.left
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

        def dump(self, node):
            print("token: " + ast.dump(node))


class VariableFinder(ast.NodeVisitor):
    variables = []

    def findVariable(self, var_name, node):
        self.variables.append(var_name)
        old_len = 0
        while len(self.variables) != old_len:
            old_len = len(self.variables)
            self.visit(node)

    def visit_Assign(self, node):
        var = self.variables[-1]
        for target in node.targets:
            if isinstance(target, ast.Name) and var == target.id:
                print "Found " + var
                if isinstance(node.value, ast.Name):
                    self.variables.add(node.value.id)
                    print node.value.id
                elif isinstance(node.value, ast.BinOp):
                    self.variables.add(node.value.left.id)
                    print node.value.left.id
                elif isinstance(node.value, ast.Str):
                    print node.value.s

    # def visit_Call(self, node):


class ConnectionChecker(ast.NodeVisitor):
    connection_libraries = {"urllib", "urllib2", "requests", "httplib", "t1mlib"}
    has_connection = False

    def check_for_connection(self, filename):
        pythonfile = open(filename, "r")
        node = ast.parse(pythonfile.read())
        self.visit(node)
        return self.has_connection


    def visit_Import(self, node):
        for token in node.names:
            if token.name in self.connection_libraries:
                self.has_connection = True
                if token.name == "SubsceneUtilities":
                    Analyzer.tempMethods.add({"geturl"})
        self.generic_visit(node)


    def visit_ImportFrom(self, node):
        for token in node.names:
            if token.name in self.connection_libraries:
                self.has_connection = True
                if token.name == "SubsceneUtilities":
                    Analyzer.tempMethods.add({"geturl"})
        self.generic_visit(node)


main()
