import os
from functions_extractor import Documenter


openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key is None or len(openai_api_key) < 10:
    openai_api_key = input("Enter your openai api key: ")

"""
DISABLED

promptlayer_api_key = os.environ.get("PROMPTLAYER_API_KEY")
if promptlayer_api_key is None or len(promptlayer_api_key) < 10:
    promptlayer_api_key = input("\nIf you want to use PromptLayer, enter your PromptLayer api key:")

promptlayer_msg = "Continuing with PromptLayer\n" if len(promptlayer_api_key) > 10 else "Continuing without PromptLayer\n"
print(promptlayer_msg)
"""


exclude_dirs = ["venv", "node_modules"]

directory = input("Enter the directory from where the functions will be extracted: ")
if len(directory) < 2:

    directory = "./"

print("Select the names of the directories to exclude from scanning, separated by commas")
print("'env' and 'node_modules' are excluded by default.")
input_exclude_dirs = input("Directories to exclude: ").split(",")

for exdir in input_exclude_dirs:
    exdir = exdir.strip()
    if len(exdir) > 0:
        exclude_dirs.append(exdir)

print(f"Excluded directories: {exclude_dirs}\n")
input('Press Enter to continue.')

#documenter = Documenter(openai_api_key, exclude_dirs, promptlayer_api_key)
documenter = Documenter(openai_api_key, exclude_dirs)
print("Loading python files...")

exclude_dirs.extend(["venv", "node_modules"])
functions = documenter.load_functions(directory, excl_dirs=exclude_dirs)
input("Press Enter to continue and document functions from all the above directories.")
documenter.document_all_functions(functions)

save_filename = input("Enter the filename where the result will be stored: ")
documenter.save_docs(save_filename, functions)