"""PDF to A5 Booklet Converter - Command Line Interface."""

import warnings
from pathlib import Path
from typing import Annotated

import typer
from slugify import slugify

from .core import convert_pdf_to_a5


def _bad_parameter(msg: str) -> None:
    raise typer.BadParameter(msg)


def pdf2a5(
    src: Annotated[
        Path,
        typer.Argument(
            help="Path to the source PDF file.",
        ),
    ],
    dst: Annotated[
        Path | None,
        typer.Argument(
            help="Path to the destination directory.",
        ),
    ] = None,
    dpi: Annotated[
        int,
        typer.Option(
            help="DPI (dots per inch) of the output PDFs.",
        ),
    ] = 300,
    batch: Annotated[
        int,
        typer.Option(
            help="Number of pages to process in a single batch.",
        ),
    ] = 4,
    shift: Annotated[
        float,
        typer.Option(
            help="Shift towards the nearest short side of the sheet.",
        ),
    ] = 0.0,
    workers: Annotated[
        int,
        typer.Option(
            help="Number of worker processes to use.",
        ),
    ] = 4,
) -> None:
    """Convert a PDF file to A5 booklet format."""
    src = src.expanduser().absolute()
    if not src.is_file():
        _bad_parameter(f"Source {src} does not exist")
    if dpi < 72:
        _bad_parameter(f"DPI {dpi} is too low")
    if batch < 1:
        _bad_parameter(f"Batch {batch} is too low")
    if batch > 10:
        warnings.warn(f"Batch {batch} is too high", stacklevel=2)
    if workers < 1:
        _bad_parameter(f"Workers {workers} is too low")

    if dst is None:
        name = slugify(src.name).removesuffix("-pdf")
        dst = Path(f"a5-{name}")
    dst = dst.expanduser().absolute()
    if not dst.is_dir():
        if not dst.parent.exists():
            _bad_parameter(f"Destination {dst} is not a directory")
        dst.mkdir(parents=False, exist_ok=True)

    convert_pdf_to_a5(
        src=src,
        dst_root=dst,
        dpi=dpi,
        batch=batch,
        workers=workers,
        shift_mm=shift,
    )


def main() -> None:  # noqa: D103
    typer.run(pdf2a5)
