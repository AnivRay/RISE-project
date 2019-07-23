import logging
import os
import ast
from collections import defaultdict, deque
import re
import sys
import draw
from usage import parse_args
from core.ast_helper import generate_ast
from cfg import make_cfg
from core.project_handler import get_modules, get_directory_modules
from analysis.constraint_table import initialize_constraint_table
from analysis.fixed_point import analyse
from web_frameworks import (FrameworkAdaptor, is_django_view_function, is_flask_route_function, is_function, is_function_without_leading_)
from vulnerabilities import (find_vulnerabilities, get_vulnerabilities_not_in_baseline)
from vulnerabilities.vulnerability_helper import SanitisedVulnerability

log = logging.getLogger(__name__)
connectionMethods = {"Request", "urlopen", "build_opener", "open", "get", "getRequest", "Session", "post"}
userInput = {"raw_input", "input", "argv", "OnKeyPress", "OnKeyRelease", "OnPosition", "OnButtonPress",
             "OnButtonRelease", "OnMotion", "ProcessMouse", "ProcessPeripherals", "Process", "OnDigitalMotion",
             "OnAnalogMotion", "ProcessMotions", "OnButtonHold", "OnButtonMotion", "OnAccelerometerMotion",
             "OnAnalogStickMotion", "OnWheelMotion", "OnThrottleMotion", "IsPressed", "OnTouchAbort",
             "OnSingleTouchStart", "OnSingleTouchHold", "OnSingleTouchMove", "OnSingleTouchEnd", "OnMultiTouchDown",
             "OnMultiTouchDown", "OnMultiTouchHold", "OnMultiTouchMove", "OnMultiTouchUp", "OnTap", "OnLongPress",
             "OnSwipe", "OnZoomPinch", "OnRotate", "OnTouchGesturePan", "OnTouchGestureEnd", "OnTouchGestureStart",
             "getText", "args"}
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
            print("file passed connection check")
            try:
                cfg = make_cfg(tree, project_modules, local_modules, path, allow_local_directory_imports=args.allow_local_imports)
                print("cfg made")
                # draw.draw_cfg(cfg, "test_output")
                '''
                with open("result_cfg2.txt", "a") as test_file:
                    test_file.write(path + "\n")
                    for node in cfg.nodes:
                        test_file.write(node.__repr__() + "\n")
                '''
                S += 1
                call_nodes = []
                input_nodes = []
                for cfg_node in cfg.nodes:
                    ast_node = cfg_node.ast_node
                    if isinstance(ast_node, ast.Call):
                        if is_connection_method(ast_node):
                            call_nodes.append(cfg_node)
                        elif is_user_input(ast_node):
                            input_nodes.append(cfg_node)
                # Get argv


                result_set = set()
                # for node in input_nodes:
                #    result_set.add(node)
                for x, n in enumerate(call_nodes):
                    with open("Analysis.txt", "a") as outFile:
                        outFile.write(path + " " + str(x) + "\n")
                        result_set.update(reverse_traverse(n, outFile))
                numHttps = 0
                numHttp = 0
                numUserInput = 0
                input_finder = ArgvChecker()
                # numUserInput += input_finder.find_args(tree)
                for node in result_set:
                    if node.label.count("https") > 0:
                        numHttps += 1
                    elif node.label.count("http") > 0:
                        numHttp += 1
                    else:
                        numUserInput += 1
                with open("Stats.txt", "a") as output:
                    output.write(path + ": http: " + str(numHttp) + " https: " + str(numHttps) + " UserInput: "
                                 + str(numUserInput) + "\n")
            except Exception as err:
                print("There was an error : " + "[" + str(path) + "]" + str(err))
                F += 1
        cfg_list = [cfg]

        framework_route_criteria = is_function
        if args.adaptor:
            if args.adaptor.lower().startswith('e'):
                framework_route_criteria = is_function
            elif args.adaptor.lower().startswith('p'):
                framework_route_criteria = is_function_without_leading_
            elif args.adaptor.lower().startswith('d'):
                framework_route_criteria = is_django_view_function

        # Add all the route functions to the cfg_list
        FrameworkAdaptor(
            cfg_list,
            project_modules,
            local_modules,
            framework_route_criteria
        )
    initialize_constraint_table(cfg_list)
    log.info("Analysing")
    analyse(cfg_list)
    log.info("Finding vulnerabilities")
    vulnerabilities = find_vulnerabilities(
        cfg_list,
        args.blackbox_mapping_file,
        args.trigger_word_file,
        args.interactive,
        nosec_lines
    )

    if args.baseline:
        vulnerabilities = get_vulnerabilities_not_in_baseline(
            vulnerabilities,
            args.baseline
        )

    args.formatter.report(vulnerabilities, args.output_file, not args.only_unsanitised)

    has_unsanitised_vulnerabilities = any(
        not isinstance(v, SanitisedVulnerability)
        for v in vulnerabilities
    )
    if has_unsanitised_vulnerabilities:
        sys.exit(1)


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
        if node.label.count("http") > 0 and isinstance(node.ast_node, ast.Assign) and has_url(node.label):
            result_set.add(node)
        for name in userInput:
            if node.label.count(name) > 0:
                # print("Found one: " + node.label)
                result_set.add(node)
    return result_set


'''
def draw_cfg():
    
    G = nx.Graph()
    G.add_node(1)
    nx.draw(G, with_labels=True, font_weight="bold")
    nx.
    
    draw.draw_cfg()
'''


def traverse(node, graph):
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
        graph.add_node(node)


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


def is_user_input(node):
    if isinstance(node.func, ast.Name) and node.func.id in userInput:
        return True
    elif isinstance(node.func, ast.Attribute) and node.func.attr in userInput:
        return True
    return False


def has_url(possible_url):
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', possible_url)
    # print(urls)
    return len(urls) > 0


class ArgvChecker(ast.NodeVisitor):
    num_argv = 0

    def find_args(self, node):
        self.visit(node)
        return self.num_argv

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == "sys" and node.attr == "argv":
            self.num_argv += 1


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
