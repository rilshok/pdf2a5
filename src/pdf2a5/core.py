import itertools
import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz  # PyMuPDF
from PIL import Image

# TODO(@rilshok): the code requires complete refactoring, built on scratch


def split_scheme(page_count: int, sheet_group: int) -> list[int]:
    sheets_count = math.ceil(page_count / 4)
    groups = [sheet_group] * math.ceil(sheets_count / sheet_group)
    idxs = itertools.cycle(range(len(groups) - 1, -1, -1))
    while sum(groups) > sheets_count:
        idx = next(idxs)
        groups[idx] = groups[idx] - 1
    result: list[int] = []
    for i, p in enumerate(groups[::-1]):
        if i % 2:
            result.append(p)
        else:
            result.insert(0, p)
    return result


def destribute_pages(page_count: int, scheme: list[int]) -> list[list[int]]:
    pages = list(range(page_count))
    pages_split: list[list[int]] = []

    current = 0
    for group in scheme:
        stop = current + group * 4
        pages_group = pages[current:stop]
        pages_split.append(pages_group)
        current = stop
    return pages_split


@dataclass
class Content:
    payload: int | None = None


@dataclass
class Page:
    left: Content
    right: Content


@dataclass
class Sheet:
    front: Page
    back: Page


#   al;ar;bl;br;
# 0  2; 3; 4; 1;
# >> 0br 0al 0ar 0bl

#   al;ar;bl;br;
# 0  4; 5; 6; 3;
# 1  2; 7; 8; 1;
# >> 1br 1al 0br 0al 0ar 0bl 1ar 1bl

#   al;ar;bl;br;
# 0  6; 7; 8; 5;
# 1  4; 9;10; 3;
# 2  2;11;12; 1;
# >> 2br 2al 1br 1al 0br 0al 0ar 0bl 1ar 1bl 2ar 2bl

#   al;ar;bl;br;
# 0  8; 9;10; 7;
# 1  6;11;12; 5;
# 2  4;13;14; 3;
# 3  2;15;16; 1;
# >> 3br 3al 2br 2al 1br 1al 0br 0al 0ar 0bl 1ar 1bl 2ar 2bl 3ar 3bl


def make_sheets(sheet_count: int, pages: list[int]):
    sheets = [
        Sheet(
            front=Page(left=Content(), right=Content()),
            back=Page(left=Content(), right=Content()),
        )
        for _ in range(sheet_count)
    ]

    contents: list[Content] = []
    for sheet in sheets[::-1]:
        contents.append(sheet.back.right)
        contents.append(sheet.front.left)

    for sheet in sheets:
        contents.append(sheet.front.right)
        contents.append(sheet.back.left)

    for content, page in zip(contents, pages, strict=True):
        content.payload = page

    # TODO(@rilshok): why contents is needed?
    return sheets


def make_a5_scheme(
    page_count: int,
    sheet_group: int,
) -> Iterator[tuple[str, list[Page]]]:
    scheme = split_scheme(page_count, sheet_group)
    page_nums = destribute_pages(page_count, scheme)

    for block, (sheet_count, pages) in enumerate(zip(scheme, page_nums, strict=True)):
        block_sheets = make_sheets(sheet_count, pages)
        yield f"{block:03}_a", [sheet.front for sheet in block_sheets]
        yield f"{block:03}_b", [sheet.back for sheet in block_sheets]


def pdf_to_image_list(save_root: Path, path: Path, dpi: int) -> list[Path]:
    # TODO(@rilshok): reduce RAM consumption
    result: list[Path] = []

    # TODO(@rilshok): open with context manager?
    pdf_document = fitz.open(path.as_posix())

    try:
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)

            image = page.get_pixmap(dpi=dpi)
            img_data = image.samples
            pil_image = Image.frombytes("RGB", (image.width, image.height), img_data)

            save_path = save_root / f"page_{page_number:05}.png"
            pil_image.save(save_path)

            result.append(save_path)
    finally:
        pdf_document.close()

    return result


def _empty_image() -> Image.Image:
    return Image.new("RGB", (1, 1), "white")


def as2_a5_page(
    image1_path: Path | None,
    image2_path: Path | None,
    dpi: int,
    save_root: Path,
    save_name: str,
) -> Path:
    # TODO(@rilshok): change image1 and image2 to path
    # A4 sheet dimensions in millimetres
    image1 = _empty_image() if image1_path is None else Image.open(image1_path)
    image2 = _empty_image() if image2_path is None else Image.open(image2_path)
    a4_width_mm = 297
    a4_height_mm = 210

    # Converting dimensions to pixels with DPI
    a4_width_px = int(a4_width_mm * dpi / 25.4)
    a4_height_px = int(a4_height_mm * dpi / 25.4)

    # blank A4 sheet with DPI
    canvas = Image.new("RGB", (a4_width_px, a4_height_px), "white")

    # the first image will be on the left
    image1_width, image1_height = image1.size
    max_width = a4_width_px // 2  # max width for the image
    max_height = a4_height_px  # max height for the image

    # scaling the first image
    if image1_width > max_width or image1_height > max_height:
        scale_factor = min(max_width / image1_width, max_height / image1_height)
        image1 = image1.resize(
            (int(image1_width * scale_factor), int(image1_height * scale_factor)),
            resample=Image.Resampling.LANCZOS,
        )

    # position for the first image (left)
    canvas.paste(image1, (0, a4_height_px // 2 - image1.height // 2))

    # the second image will be on the right
    image2_width, image2_height = image2.size

    # scaling the second image
    if image2_width > max_width or image2_height > max_height:
        scale_factor = min(max_width / image2_width, max_height / image2_height)
        image2 = image2.resize(
            (int(image2_width * scale_factor), int(image2_height * scale_factor)),
            resample=Image.Resampling.LANCZOS,
        )

    # position for the second image (right, maximum right)
    canvas.paste(
        image2,
        (a4_width_px - image2.width, a4_height_px // 2 - image2.height // 2),
    )

    save_path = save_root / f"{save_name}.png"
    canvas.save(save_path)
    return save_path


def _write_pdf(root: Path, name: str, image_paths: list[Path]) -> Path:
    image_list = [Image.open(p) for p in image_paths]
    save_path = root / f"{name}.pdf"
    image_list[0].save(save_path, save_all=True, append_images=image_list[1:])
    return save_path


def convert_pdf_to_a5(src: Path, dst_root: Path, dpi: int, batch: int) -> None:
    with TemporaryDirectory() as tmpdir:
        root_raw = Path(tmpdir) / "raw"
        root_raw.mkdir(parents=False, exist_ok=False)
        image_paths = pdf_to_image_list(save_root=root_raw, path=src, dpi=dpi)

        scheme_ = make_a5_scheme(len(image_paths), batch)
        scheme = [
            (name, [(p.left.payload, p.right.payload) for p in pages])
            for (name, pages) in scheme_
        ]

        root_pages = Path(tmpdir) / "pages"
        root_pages.mkdir(parents=False, exist_ok=False)
        for name, pages_scheme in scheme:
            page_paths = [
                as2_a5_page(
                    image1_path=None if left is None else image_paths[left],
                    image2_path=None if right is None else image_paths[right],
                    dpi=dpi,
                    save_root=root_pages,
                    save_name=f"{name}_{i:05}",
                )
                for i, (left, right) in enumerate(pages_scheme)
            ]
            _write_pdf(root=dst_root, name=name, image_paths=page_paths)
