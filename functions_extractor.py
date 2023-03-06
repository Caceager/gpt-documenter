import ast
import json
from typing import List
import os
from typing import Any
from pydantic import BaseModel
from querier import Querier
from templates import doc_function_template, doc_base_function_template, summary_json_template


class FunctionDeclaration(BaseModel):
    function_name: str
    function_args: str
    partial_function_name: str
    function_body: Any
    functions_inside: List[str] = []
    object_name: str | None = None
    function_docs: dict | None = None


class Documenter:
    def __init__(
            self,
            openai_api_key: str,
            exclude_directories: list[str] = [],
            promptlayer_api_key: str | None = None
            ):
        self.querier = Querier(openai_api_key=openai_api_key,
                               promptlayer_api_key=promptlayer_api_key)
        self.exclude_directories = exclude_directories

    def function_string(self, function: FunctionDeclaration):
        return f"""
        function name: {function.function_name}\n
        function args: {function.function_args}\n
        function body: {function.function_body}\n
        """

    def select_functions_names(self, functions: List[FunctionDeclaration]):
        for main_i, function in enumerate(functions):
            name = function.function_name
            body = function.function_body
            for comp_i, fun in enumerate(functions):
                comp_name = fun.function_name
                if comp_name != name and fun.function_body == body:
                    shortest_named_index = main_i if len(name) < len(comp_name) else comp_i
                    functions.pop(shortest_named_index)

        return functions
    def extract_functions(self, file_path: str) -> List[FunctionDeclaration]:
        print(file_path)
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())

        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                node_body = ast.unparse(node.body)
                args = ast.unparse(node.args)
                functions.append(
                    FunctionDeclaration(function_name=node.name, function_body=node_body, function_args=args,
                                        partial_function_name=node.name))

            elif isinstance(node, ast.ClassDef):
                for subnode in node.body:
                    if isinstance(subnode, ast.FunctionDef):
                        args = ast.unparse(subnode.args)
                        subnode_body = ast.unparse(subnode.body)
                        function_name = f"{node.name}.{subnode.name}"
                        functions.append(FunctionDeclaration(
                            function_name=function_name, function_body=subnode_body, function_args=args,
                            object_name=node.name, partial_function_name=subnode.name
                            )
                        )

        return self.select_functions_names(functions)

    def load_functions(self, directory: str, excl_dirs: List[str] = []):
        functions = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isdir(file_path):
                # If the current file is a directory, recursively call the function to load functions from the subdirectory
                if os.path.basename(file_path) not in excl_dirs:
                    functions.extend(self.load_functions(file_path, excl_dirs))
            elif filename.endswith(".py") and os.path.basename(file_path) not in excl_dirs:
                # If the current file is a Python file, extract functions from it
                functions.extend(self.extract_functions(file_path))

        return functions

    def add_used_functions(self, functions: List[FunctionDeclaration]):
        functions_names = []
        for function in functions:
            functions_names.append(function.partial_function_name)

        for function_name in functions_names:
            cast_name = f"{function_name}("
            for function in functions:
                if cast_name in function.function_body and function_name != function.partial_function_name:
                    function.functions_inside.append(function_name)

    def document_all_functions(self, functions: list[FunctionDeclaration]):
        self.add_used_functions(functions)
        ordered_functions = sorted(functions, key=lambda x: len(x.functions_inside))
        for of in ordered_functions:
            self.enqueue_function(of, functions)

    def doc_base_function(self, function: FunctionDeclaration):
        template = doc_base_function_template()
        fstring = self.function_string(function)
        pl_tags = ["base function", function.function_name]
        response = self.querier.send_query(
            prompt=template, pl_tags=pl_tags, language="Python", text=fstring,
            summary_json_template=summary_json_template(),
        )
        response.replace("\n", "")
        function_docs = json.loads(response)
        function.function_docs = function_docs
        print(f"Documented function: {function.function_name}")
        return function_docs


    def doc_function(self, function: FunctionDeclaration, inside_funtions: list[FunctionDeclaration]):
        fstring = self.function_string(function)
        inside_function_docs = [str(func.function_docs) for func in inside_funtions]
        context = "\n-->".join(inside_function_docs)
        template = doc_function_template()
        pl_tags = ["composed function", function.function_name]
        response = self.querier.send_query(
            prompt=template, language="Python", pl_tags=pl_tags, text=fstring, summary_json_template=summary_json_template(),
            summaries=context
        )
        response.replace("\n", "")
        function_docs = json.loads(response)
        function.function_docs = function_docs
        print(f"Documented function: {function.function_name}")

        return function_docs

    def enqueue_function(self, function: FunctionDeclaration, functions: list[FunctionDeclaration]):
        if function.function_docs is not None:
            return
        elif len(function.functions_inside) == 0:
            return self.document_function(function)
        else:
            inside_functions = list(filter(lambda obj: obj.partial_function_name in function.functions_inside, functions))
            for fun in inside_functions:
                self.enqueue_function(fun, functions)
            return self.document_function(function, inside_functions)

    def document_function(
            self,
            function: FunctionDeclaration,
            inside_functions: list[FunctionDeclaration] | None = None
    ):
        function.function_docs = self.doc_function(function, inside_functions) \
            if len(function.functions_inside) > 0 \
            else self.doc_base_function(function)
        function.function_docs["function_name"] = function.partial_function_name

    def save_docs(self, filename: str, functions):
        docs_list = []
        for function in functions:
            if function.function_docs is not None:
                function.function_docs["function_name"] = function.function_name
                docs_list.append(function.function_docs)

        with open(f"{filename}.json", "w") as res:
            res.write(json.dumps(docs_list, indent=2))
        print(f"Docs saved in file: {filename}.json")