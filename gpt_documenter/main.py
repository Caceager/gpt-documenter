from typing import List
from gpt_documenter.documenter import Documenter
import typer

app = typer.Typer()


@app.command()
def document_functions(
        openai_api_key: str,
        project_path: str,
        output_path: str,
        excluded_dirs: List[str] = typer.Argument(None)
        ):
    documenter = Documenter(openai_api_key, excluded_dirs)
    excluded_dirs.extend(["venv", "node_modules"])
    functions = documenter.load_functions(project_path, excl_dirs=excluded_dirs)
    documenter.document_all_functions(functions)
    documenter.save_docs(output_path, functions)


@app.command()
def inspect(
        project_path: str,
        output_path: str,
        excluded_paths: List[str] = typer.Argument(None)
            ):
    excluded_paths.extend(["venv", "node_modules"])
    typer.echo(f"\nExcluded dirs: {excluded_paths}")
    documenter = Documenter(exclude_directories=excluded_paths)
    functions = documenter.load_functions(project_path, excl_dirs=excluded_paths)
    typer.echo("Files to be documented: ")
    for path in documenter.path_list:
        typer.echo(path)

    estimated_token_usage, estimated_cost_usd = \
        documenter.estimate_token_usage(functions)
    typer.echo(f"Estimated token usage: {estimated_token_usage}")
    typer.echo(f"Estimated cost in USD: {estimated_cost_usd}")
    typer.echo(f"\nOutput filename: {output_path}.json")


if __name__ == "__main__":
    app()
