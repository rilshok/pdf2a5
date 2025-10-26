import itertools
import math
import os
from collections.abc import Iterator
from concurrent.futures import FIRST_EXCEPTION, ProcessPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz  # PyMuPDF
from PIL import Image, ImageChops


from collections.abc import Container


def _random_name() -> str:
    return os.urandom(32).hex()


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
        yield f"{block + 1:03}_a", [sheet.back for sheet in block_sheets][::-1]
        yield f"{block + 1:03}_b", [sheet.front for sheet in block_sheets]


def _read_number_of_pages(pdf_path: Path) -> int:
    pdf_document = fitz.open(pdf_path.as_posix())
    try:
        return len(pdf_document)
    finally:
        pdf_document.close()


def _empty_image() -> Image.Image:
    return Image.new("RGB", (1, 1), "white")


def as2_a5_page(
    image1_path: Path | None,
    image2_path: Path | None,
    dpi: int,
    save_root: Path,
    fold_mm: float,
    shift_mm: float,
) -> Path:
    # A4 sheet dimensions in millimetres
    image1 = _empty_image() if image1_path is None else Image.open(image1_path)
    image2 = _empty_image() if image2_path is None else Image.open(image2_path)
    a4_width_mm = 297
    a4_height_mm = 210

    # Converting dimensions to pixels with DPI
    fold_px = int(fold_mm * dpi / 25.4)
    shift_px = int(shift_mm * dpi / 25.4)
    a4_width_px = int(a4_width_mm * dpi / 25.4)
    a4_height_px = int(a4_height_mm * dpi / 25.4)

    # blank A4 sheet with DPI
    canvas = Image.new("RGB", (a4_width_px, a4_height_px), "white")

    # the first image will be on the left
    image1_width, image1_height = image1.size
    max_width = a4_width_px // 2 - fold_px  # max width for the image
    max_height = a4_height_px  # max height for the image

    # scaling the first image
    if image1_width > max_width or image1_height > max_height:
        scale_factor = min(max_width / image1_width, max_height / image1_height)
        image1 = image1.resize(
            (int(image1_width * scale_factor), int(image1_height * scale_factor)),
            resample=Image.Resampling.LANCZOS,
        )

    # position for the first image (left)
    canvas.paste(
        image1,
        (0 - shift_px, a4_height_px // 2 - image1.height // 2),
    )

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
        (
            a4_width_px - image2.width + shift_px,
            a4_height_px // 2 - image2.height // 2,
        ),
    )

    save_path = save_root / f"{_random_name()}.png"
    canvas.save(save_path)
    return save_path


def _write_pdf(save_path: Path, image_paths: list[Path]) -> Path:
    head, tail = Image.open(image_paths[0]), (Image.open(p) for p in image_paths[1:])
    head.save(save_path, save_all=True, append_images=tail)
    return save_path


def trim_white_borders(image: Image.Image) -> Image.Image:
    bg = Image.new(image.mode, image.size, (255, 255, 255))
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if bbox:
        trimmed_image = image.crop(bbox)
        return trimmed_image
    return image


def _export_page_images(
    src: Path,
    pages: list[int],
    save_root: Path,
    *,
    dpi: int,
    crop: bool,
    skip_crop: Container[int],
) -> list[Path]:
    result: list[Path] = []
    document = fitz.open(src.as_posix())
    try:
        for page_number in pages:
            page = document.load_page(page_number)
            image = page.get_pixmap(dpi=dpi)
            img_data = image.samples
            size = (image.width, image.height)
            pil_image = Image.frombytes("RGB", size, img_data)
            if crop and page_number not in skip_crop:
                pil_image = trim_white_borders(pil_image)
            save_path = save_root / f"{_random_name()}.png"
            pil_image.save(save_path)
            result.append(save_path)
    finally:
        document.close()
    return result


def _build_sub_pdf(
    src: Path,
    pages: list[tuple[int | None, int | None]],
    *,
    save_path: Path,
    dpi: int,
    fold_mm: float,
    shift_mm: float,
    crop: bool,
    skip_crop: Container[int],
) -> None:
    page_nums = [n for page in pages for n in page if n is not None]
    with TemporaryDirectory() as tmpdir:
        root_temp = Path(tmpdir)
        single_page_paths: dict[int | None, Path | None] = dict(
            zip(
                page_nums,
                _export_page_images(
                    src=src,
                    pages=page_nums,
                    save_root=root_temp,
                    dpi=dpi,
                    crop=crop,
                    skip_crop=skip_crop,
                ),
                strict=True,
            )
        )
        single_page_paths[None] = None
        page_paths = [
            as2_a5_page(
                image1_path=single_page_paths[left],
                image2_path=single_page_paths[right],
                dpi=dpi,
                save_root=root_temp,
                fold_mm=fold_mm,
                shift_mm=shift_mm,
            )
            for left, right in pages
        ]
        _write_pdf(save_path=save_path, image_paths=page_paths)


def convert_pdf_to_a5(
    src: Path,
    dst_root: Path,
    *,
    dpi: int,
    batch: int,
    fold_mm: float,
    shift_mm: float,
    crop: bool,
    workers: int,
    skip_crop: Container[int],
) -> None:
    page_count = _read_number_of_pages(src)
    if batch * 4 > page_count:
        batch = math.ceil(page_count / 4)
    scheme: dict[str, list[tuple[int | None, int | None]]] = {
        name: [(p.left.payload, p.right.payload) for p in pages]
        for name, pages in make_a5_scheme(page_count, batch)
    }
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _build_sub_pdf,
                src=src,
                pages=pages,
                save_path=dst_root / f"{name}.pdf",
                dpi=dpi,
                fold_mm=fold_mm,
                shift_mm=shift_mm,
                crop=crop,
                skip_crop=skip_crop,
            )
            for name, pages in scheme.items()
        ]
        done, not_done = wait(futures, return_when=FIRST_EXCEPTION)
        for future in done:
            if (exception := future.exception()) is None:
                continue
            for f in not_done:
                f.cancel()
            raise exception
