import logging
import os
import sys
import ast
from collections import defaultdict, deque
import time
from usage import parse_args
from core.ast_helper import generate_ast
from cfg import make_cfg
from core.project_handler import get_modules, get_directory_modules

from build.lib.pyt.web_frameworks import (FrameworkAdaptor, is_django_view_function, is_flask_route_function, is_function, is_function_without_leading_)

log = logging.getLogger(__name__)
connectionMethods = {"Request", "urlopen", "build_opener", "open", "get", "getRequest", "Session", "post"}
connectionClasses = {"self", "urllib", "urllib2", "requests", "httplib", "t1mlib", "session"}
S = 0.0
F = 0.0


def discover_files(targets, excluded_files, recursive=False):
    included_files = list()
    excluded_list = excluded_files.split(",")
    for target in targets:
        if os.path.isdir(target):
            for root, _, files in os.walk(target):
                for file in files:
                    if file.endswith('.py') and file not in excluded_list:
                        fullpath = os.path.join(root, file)
                        included_files.append(fullpath)
                        log.debug('Discovered file: %s', fullpath)
                if not recursive:
                    break
        else:
            if target not in excluded_list:
                included_files.append(target)
                log.debug('Discovered file: %s', target)

    return included_files


def retrieve_nosec_lines(
    path
):
    file = open(path, 'r')
    lines = file.readlines()
    return set(
        lineno for
        (lineno, line) in enumerate(lines, start=1)
        if '#nosec' in line or '# nosec' in line
    )


def main(dirname):  # noqa: C901
    global S
    global F
    command_line_args = [dirname, "-r"]
    args = parse_args(command_line_args)

    logging_level = (
        logging.ERROR if not args.verbose else
        logging.WARN if args.verbose == 1 else
        logging.INFO if args.verbose == 2 else
        logging.DEBUG
    )
    logging.basicConfig(level=logging_level, format='[%(levelname)s] %(name)s: %(message)s')

    files = discover_files(
        args.targets,
        args.excluded_paths,
        args.recursive
    )

    nosec_lines = defaultdict(set)

    if args.project_root:
        directory = os.path.normpath(args.project_root)
        project_modules = get_modules(directory, prepend_module_root=args.prepend_module_root)

    for path in sorted(files):
        print(path)
        log.info("Processing %s", path)
        if not args.ignore_nosec:
            nosec_lines[path] = retrieve_nosec_lines(path)
        if not args.project_root:
            directory = os.path.dirname(path)
            project_modules = get_modules(directory, prepend_module_root=args.prepend_module_root)

        local_modules = get_directory_modules(directory)
        tree = generate_ast(path)
        connection_checker = ConnectionChecker()
        if connection_checker.check_for_connection(tree):
            print("passed")
            try:
                cfg = make_cfg(tree, project_modules, local_modules, path, allow_local_directory_imports=args.allow_local_imports)
                print("cfg made")
                with open("result_cfg2.txt", "a") as test_file:
                    test_file.write(path + "\n")
                    for node in cfg.nodes:
                        test_file.write(node.__repr__() + "\n")
                S += 1
                call_nodes = []
                for cfg_node in cfg.nodes:
                    ast_node = cfg_node.ast_node
                    if isinstance(ast_node, ast.Call) and is_connection_method(ast_node):
                        call_nodes.append(cfg_node)
                result_set = set()
                for x, n in enumerate(call_nodes):
                    with open("Analysis.txt", "a") as outFile:
                        outFile.write(path + " " + str(x) + "\n")
                        result_set.update(reverse_traverse(n, outFile))
                numHttps = 0
                numHttp = 0
                for node in result_set:
                    if node.label.count("https") > 0:
                        numHttps += 1
                    elif node.label.count("http") > 0:
                        numHttp += 1
                with open("Stats.txt", "a") as output:
                    output.write(path + ": http: " + str(numHttp) + " https: " + str(numHttps) + "\n")
            except Exception as err:
                print("There was an error : " + "[" + str(path) + "]" + str(err))
                F += 1


def reverse_traverse(node, file):
    result_set = set()
    linked_list = deque()
    visited = set()
    linked_list.append(node)
    visited.add(node)
    while len(linked_list) > 0:
        node = linked_list.popleft()
        for parent in node.ingoing:
            if parent not in visited:
                linked_list.append(parent)
                visited.add(parent)
        file.write(node.__repr__() + "\n")
        node.label = node.label.lower()
        if node.label.count("http") > 0:
            result_set.add(node)
    return result_set


def traverse(node, num):
    with open(str(num) + "_traversal.txt", "a") as outFile:
        linked_list = deque()
        visited = set()
        linked_list.append(node)
        visited.add(node)
        while len(linked_list) > 0:
            node = linked_list.popleft()
            for child in node.outgoing:
                if child not in visited:
                    linked_list.append(child)
                    visited.add(child)
            ast_node = node.ast_node
            if ast_node is not None and isinstance(ast_node, ast.Call):
                print_ast_func_name(ast_node, outFile)
                outFile.write(node.__repr__() + "\n")


def print_ast_func_name(node, file):
    if isinstance(node.func, ast.Name):
        file.write("is name: " + node.func.id + "\n")
    elif isinstance(node.func, ast.Attribute):
        file.write("is attribute: " + node.func.attr + "\n")
    else:
        file.write("something else: " + node.__str__() + "\n")


def is_connection_method(node):
    if isinstance(node.func, ast.Name) and node.func.id in connectionMethods:
        return True
    elif isinstance(node.func, ast.Attribute) and node.func.attr in connectionMethods:
        if isinstance(node.func.value, ast.Name) and node.func.value.id not in connectionClasses:  # Prefix is wrong
            return False
        else:
            return True
    return False


class ConnectionChecker(ast.NodeVisitor):
    connection_libraries = {"urllib", "urllib2", "requests", "httplib", "t1mlib"}
    has_connection = False

    def check_for_connection(self, node):
        self.visit(node)
        return self.has_connection

    def visit_Import(self, node):
        for token in node.names:
            if self.is_connection_library(token.name):
                self.has_connection = True
        self.generic_visit(node)


    def visit_ImportFrom(self, node):
        for token in node.names:
            if self.is_connection_library(token.name):
                self.has_connection = True
        self.generic_visit(node)

    def is_connection_library(self, token):
        for lib in self.connection_libraries:
            if token.count(lib) > 0:
                return True
        return False
