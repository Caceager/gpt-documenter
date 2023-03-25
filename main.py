from typing import List
from documenter import Documenter
import typer

app = typer.Typer()


@app.command()
def document_functions(
        api_key: str,
        path: str,
        output_filename: str,
        excluded_dirs: List[str] = typer.Argument(None)
        ):
    documenter = Documenter(api_key, excluded_dirs)
    excluded_dirs.extend(["venv", "node_modules"])
    functions = documenter.load_functions(path, excl_dirs=excluded_dirs)
    documenter.document_all_functions(functions)
    documenter.save_docs(output_filename, functions)


@app.command()
def inspect(
        path: str,
        output_filename: str,
        excluded_dirs: List[str] = typer.Argument(None)
            ):
    excluded_dirs.extend(["venv", "node_modules"])
    typer.echo(f"\nExcluded dirs: {excluded_dirs}")
    documenter = Documenter("", excluded_dirs)
    functions = documenter.load_functions(path, excl_dirs=excluded_dirs)
    typer.echo("Files to be documented: ")
    for path in documenter.path_list:
        typer.echo(path)

    estimated_token_usage, estimated_cost_usd = \
        documenter.estimate_token_usage(functions)
    typer.echo(f"Estimated token usage: {estimated_token_usage}")
    typer.echo(f"Estimated cost in USD: {estimated_cost_usd}")
    typer.echo(f"\nOutput filename: {output_filename}.json")


if __name__ == "__main__":
    app()
