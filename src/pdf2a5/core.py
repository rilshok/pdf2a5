import itertools
import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image

# TODO(@rilshok): the code requires complete refactoring, built on scratch


def split_scheme(page_count, sheet_group):
    sheets_count = math.ceil(page_count / 4)
    groups = [sheet_group] * math.ceil(sheets_count / sheet_group)
    idxs = itertools.cycle(range(len(groups) - 1, -1, -1))
    while sum(groups) > sheets_count:
        idx = next(idxs)
        groups[idx] = groups[idx] - 1
    result = []
    for i, p in enumerate(groups[::-1]):
        if i % 2:
            result.append(p)
        else:
            result.insert(0, p)
    return result


def destribute_pages(page_count, scheme: list[int]):
    pages = list(range(page_count))
    pages_split = []

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


#   fl;fr;bl;br;
# 0  2; 3; 4; 1;
# >> 0br 0fl 0fr 0bl

#   fl;fr;bl;br;
# 0  4; 5; 6; 3;
# 1  2; 7; 8; 1;
# >> 1br 1fl 0br 0fl 0fr 0bl 1fr 1bl

#   fl;fr;bl;br;
# 0  6; 7; 8; 5;
# 1  4; 9;10; 3;
# 2  2;11;12; 1;
# >> 2br 2fl 1br 1fl 0br 0fl 0fr 0bl 1fr 1bl 2fr 2bl

#   fl;fr;bl;br;
# 0  8; 9;10; 7;
# 1  6;11;12; 5;
# 2  4;13;14; 3;
# 3  2;15;16; 1;
# >> 3br 3fl 2br 2fl 1br 1fl 0br 0fl 0fr 0bl 1fr 1bl 2fr 2bl 3fr 3bl


def make_sheets(sheet_count: int, pages: list[int]):
    sheets = [
        Sheet(
            front=Page(left=Content(), right=Content()),
            back=Page(left=Content(), right=Content()),
        )
        for _ in range(sheet_count)
    ]

    contents = []
    for sheet in sheets[::-1]:
        contents.append(sheet.back.right)
        contents.append(sheet.front.left)

    for sheet in sheets:
        contents.append(sheet.front.right)
        contents.append(sheet.back.left)

    for content, page in zip(contents, pages):
        content.payload = page

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


def pdf_to_image_list(path: Path, dpi: int) -> list[Image.Image]:
    result: list[Image.Image] = []

    # TODO(@rilshok): open with context manager?
    pdf_document = fitz.open(path.as_posix())

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        image = page.get_pixmap(dpi=dpi)
        img_data = image.samples
        pil_image = Image.frombytes("RGB", [image.width, image.height], img_data)

        result.append(pil_image)

    pdf_document.close()

    return result


def as2_a5_page(image1: Image.Image, image2: Image.Image, dpi: int) -> Image.Image:
    # A4 sheet dimensions in millimetres
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
            Image.LANCZOS,
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
            Image.LANCZOS,
        )

    # position for the second image (right, maximum right)
    canvas.paste(
        image2,
        (a4_width_px - image2.width, a4_height_px // 2 - image2.height // 2),
    )

    return canvas


def images_to_pdf(root: Path, name: str, images: list[Image.Image]) -> None:
    save_path = root / f"{name}.pdf"
    images[0].save(save_path, save_all=True, append_images=images[1:])


def convert_pdf_to_a5(src: Path, dst_root: Path, dpi: int, batch: int) -> None:
    images = pdf_to_image_list(path=src, dpi=dpi)

    scheme_ = make_a5_scheme(len(images), batch)
    scheme = [
        (name, [(p.left.payload, p.right.payload) for p in pages])
        for (name, pages) in scheme_
    ]

    preresults = {
        name: [
            as2_a5_page(
                images[left] if left is not None else Image.new("RGB", (1, 1), "white"),
                images[right]
                if right is not None
                else Image.new("RGB", (1, 1), "white"),
                dpi=dpi,
            )
            for left, right in pages_scheme
        ]
        for (name, pages_scheme) in scheme
    }

    for name, images__ in preresults.items():
        images_to_pdf(root=dst_root, name=name, images=images__)
