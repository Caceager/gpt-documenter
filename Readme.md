# GPT-Documenter

GPT-Documenter is a small project that automates the process of documenting Python functions by using GPT-3.5 along with Langchain.

## Installation

# -

```shell
git clone https://github.com/username/gpt-documenter.git
```


## Usage

GPT-Documenter utilizes Python Typer and provides two main commands:

1. `inspect`
2. `document-functions`

### inspect

The `inspect` command allows you to preview the documentation setup and receive an estimate of token usage. To use the `inspect` command, provide the following parameters:

- `project_path`: The path of the project you want to document
- `output_path`: The path where the JSON result will be saved
- `excluded_paths`: A list of paths you want to avoid, with project_path as root.

Here's an example of how to use the `inspect` command:

```shell
python main.py inspect /path/to/project /path/to/output.json directory/to/avoid, file_to_avoid.py
```


### document-functions

The `document-functions` command generates the actual documentation for the Python functions in your project. You'll need to provide the same arguments as the `inspect` command, along with your OpenAI API key:

- `openai_api_key`: Your OpenAI API key
- `project_path`: The path of the project you want to document
- `output_path`: The path where the JSON result will be saved
- `exclude_paths`: A list of paths you want to avoid, with project_path as root.

Here's an example of how to use the `document-functions` command:
```shell
python main.py document-functions YOUR_API_KEY /path/to/project /path/to/output.json directory/to/avoid, file_to_avoid.py
```

Once the command is executed, GPT-Documenter will begin generating the documentation for the functions and save the result as a JSON file in the specified output path.

