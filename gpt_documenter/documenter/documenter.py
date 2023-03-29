import ast
import json
from typing import List
import os
from typing import Any
from pydantic import BaseModel

from gpt_documenter.utils import utils
from gpt_documenter.querier import Querier
from .templates import doc_function_template, doc_base_function_template, summary_json_template


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
            openai_api_key: str = None,
            exclude_directories: list[str] = [],
            ):
        self.path_list = []
        self.querier = Querier(openai_api_key=openai_api_key)
        self.exclude_directories = exclude_directories
        self.total_functions = 0
        self.progress = 1

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
        self.path_list.append(file_path)
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
                # If the current file is a directory, recursively call the function
                # to load functions from the subdirectory
                if os.path.basename(file_path) not in excl_dirs:
                    functions.extend(self.load_functions(file_path, excl_dirs))
            elif filename.endswith(".py") and os.path.basename(file_path) not in excl_dirs:
                # If the current file is a Python file, extract functions from it
                functions.extend(self.extract_functions(file_path))
        self.total_functions = len(functions)
        self.add_used_functions(functions)
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

    def estimate_token_usage(self, functions: [FunctionDeclaration]):
        token_usage = 0
        for function in functions:
            function_text = function.function_body \
                + function.function_args + function.partial_function_name
            functions_used = len(function.functions_inside)
            token_usage += self.querier.calculate_function_tokens(function_text, functions_used)

        estimated_cost_usd = (token_usage / 1000) * 0.002
        return token_usage, estimated_cost_usd

    def get_ordered_functions(self, function: FunctionDeclaration, functions: list[FunctionDeclaration],
                              ordered_functions: list[FunctionDeclaration], visited_functions: set):
        if function.partial_function_name in visited_functions:
            return
        elif function in ordered_functions:
            return
        visited_functions.add(function.partial_function_name)
        for inner_func_name in function.functions_inside:
            inner_func = next((f for f in functions if f.partial_function_name == inner_func_name), None)
            if inner_func is not None:
                self.get_ordered_functions(inner_func, functions, ordered_functions, visited_functions)
        ordered_functions.append(function)

    def get_ordered_function_list(self, functions: list[FunctionDeclaration]) -> list[FunctionDeclaration]:
        ordered_functions = []
        visited_functions = set()
        for f in functions:
            try:
                self.get_ordered_functions(f, functions, ordered_functions, visited_functions)
            except Exception as err:
                print(f"An error has occurred while enqueueing function: {f.function_name}.")
                raise err
        return ordered_functions

    def document_all_functions(self, functions: list[FunctionDeclaration]):
        ordered_functions = self.get_ordered_function_list(functions)
        for function in ordered_functions:
            inside_functions = list(
                filter(
                    lambda obj: obj.partial_function_name in function.functions_inside,
                    functions
                )
            )
            self.document_function(function, inside_functions)

    def doc_base_function(self, function: FunctionDeclaration):
        template = doc_base_function_template()
        fstring = self.function_string(function)
        pl_tags = ["base function", function.function_name]
        print(f"Documenting function: {function.function_name} ({self.progress}/{self.total_functions})")
        response = self.querier.send_query(
            prompt=template, language="Python", text=fstring,
            summary_json_template=summary_json_template(),
        )
        response.replace("\n", "")
        function_docs = utils.json_load(response)
        function.function_docs = function_docs
        print(f"Result: {response}")
        return function_docs

    def doc_function(self, function: FunctionDeclaration, inside_funtions: list[FunctionDeclaration]):
        fstring = self.function_string(function)
        inside_function_docs = [str(func.function_docs) for func in inside_funtions]
        context = "\n-->".join(inside_function_docs)
        template = doc_function_template()
        pl_tags = ["composed function", function.function_name]
        print(f"Documenting function: {function.function_name} ({self.progress}/{self.total_functions})")

        response = self.querier.send_query(
            prompt=template, language="Python", text=fstring, summary_json_template=summary_json_template(),
            summaries=context
        )
        response.replace("\n", "")
        print(f"Result: {response}")
        function_docs = utils.json_load(response)
        function.function_docs = function_docs

        return function_docs

    def document_function(
            self,
            function: FunctionDeclaration,
            inside_functions: list[FunctionDeclaration] | None = None
    ):
        try:
            function.function_docs = self.doc_function(function, inside_functions) \
                if len(function.functions_inside) > 0 \
                else self.doc_base_function(function)
            function.function_docs["function_name"] = function.partial_function_name
        except Exception as err:
            print(f"Error ocurred while documenting function {function.function_name}:\n {err}")
            function.function_docs = ""

        self.progress += 1

    def save_docs(self, filename: str, functions):
        docs_list = []
        for function in functions:
            if function.function_docs is not None:
                function.function_docs["function_name"] = function.function_name
                docs_list.append(function.function_docs)

        with open(f"{filename}.json", "w") as res:
            res.write(json.dumps(docs_list, indent=2))
        print(f"Docs saved in file: {filename}.json")

        with open(f"{filename}-prompt_data.json", "w") as res:
            res.write(json.dumps(self.querier.prompts_sent, indent=2))

        total_token_usage = 0
        for prompt in self.querier.prompts_sent:
            total_token_usage += prompt["token_usage"]

        print(f"Total token usage: {total_token_usage}")