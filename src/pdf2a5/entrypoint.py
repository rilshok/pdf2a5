"""PDF to A5 Booklet Converter - Command Line Interface."""

import warnings
from pathlib import Path
from typing import Annotated

import typer

from .core import convert_pdf_to_a5


def _bad_parameter(msg: str) -> None:
    raise typer.BadParameter(msg)


def pdf2a5(
    source: Annotated[
        Path,
        typer.Argument(
            help="Path to the source PDF file.",
        ),
    ],
    dest: Annotated[
        Path | None,
        typer.Argument(
            help="Path to the destination directory.",
        ),
    ] = Path(),
    dpi: Annotated[
        int,
        typer.Option(
            help="DPI (dots per inch) of the output PDFs.",
        ),
    ] = 120,
    batch: Annotated[
        int,
        typer.Option(
            help="Number of pages to process in a single batch.",
        ),
    ] = 2,
) -> None:
    """Convert a PDF file to A5 booklet format."""
    source = source.expanduser().absolute()
    dest = dest.expanduser().absolute() if dest else source.parent
    if not source.is_file():
        _bad_parameter(f"Source {source} does not exist")
    if not dest.is_dir():
        _bad_parameter(f"Destination {dest} is not a directory")
    if dpi < 72:
        _bad_parameter(f"DPI {dpi} is too low")
    if batch < 1:
        _bad_parameter(f"Batch {batch} is too low")
    if batch > 10:
        warnings.warn(f"Batch {batch} is too high", stacklevel=2)
    convert_pdf_to_a5(source=source, dest=dest, dpi=dpi, batch=batch)


def main() -> None:  # noqa: D103
    typer.run(pdf2a5)
