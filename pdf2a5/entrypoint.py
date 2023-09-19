from pathlib import Path
from typing import Optional

import typer

from .core import convert_pdf_to_a5


def pdf2a5(source: Path, dest: Optional[Path] = None, dpi: int = 120):
    source = source.expanduser().absolute()
    dest = dest.expanduser().absolute() if dest else source.parent
    if not source.exists():
        raise typer.BadParameter(f"Source {source} does not exist")
    if not dest.is_dir():
        raise typer.BadParameter(f"Destination {dest} is not a directory")
    if dpi < 72:
        raise typer.BadParameter(f"DPI {dpi} is too low")
    convert_pdf_to_a5(source=source, dest=dest, dpi=dpi)


def main():
    typer.run(pdf2a5)
