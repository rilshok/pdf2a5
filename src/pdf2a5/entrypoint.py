import warnings
from pathlib import Path

import typer

from .core import convert_pdf_to_a5


def pdf2a5(source: Path, dest: Path | None = None, dpi: int = 120, batch: int = 5):
    source = source.expanduser().absolute()
    dest = dest.expanduser().absolute() if dest else source.parent
    if not source.exists():
        raise typer.BadParameter(f"Source {source} does not exist")
    if not dest.is_dir():
        raise typer.BadParameter(f"Destination {dest} is not a directory")
    if dpi < 72:
        raise typer.BadParameter(f"DPI {dpi} is too low")
    if batch < 1:
        raise typer.BadParameter(f"Batch {batch} is too low")
    if batch > 10:
        warnings.warn(f"Batch {batch} is too high")
    convert_pdf_to_a5(source=source, dest=dest, dpi=dpi, batch=batch)


def main():
    typer.run(pdf2a5)
