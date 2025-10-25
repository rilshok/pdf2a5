# PDF to A5 Booklet Converter

PDF to A5 Booklet Converter is a command-line tool designed to help you print PDF documents as booklets on A5-sized sheets. This tool splits the PDF pages into A5-sized pairs, allowing you to print them double-sided and then manually bind them into a booklet. It is especially useful for DIY printing and binding of various documents, such as brochures, manuals, or small books.

## Key Features

- Converts PDF documents into A5-sized booklet format.
- Splits the PDF pages into pairs, suitable for double-sided printing.
- Allows customization of the number of pages in each batch.
- Maintains the original content layout while resizing pages to fit the A5 format.
- Outputs each batch of pages as separate PDF files for easy printing and assembly.

## Installation

To use the PDF to A5 Booklet Converter, follow these steps:

1. Clone or download the repository to your local machine.
2. Make sure you have Python 3.11 or higher installed.
3. Install the module project directory by `pip install .`

## Usage

The command-line interface allows you to easily convert PDF files into A5 booklets. Here's how to use it:

```bash
pdf2a5 SOURCE_PDF [DESTINATION_DIRECTORY] [OPTIONS]
```

- `SOURCE_PDF` (string): The path to the source PDF file you want to convert.
- `DESTINATION_DIRECTORY` (optional string): The directory where the converted PDF booklets will be saved. If not provided, the tool will create a directory for the output files in the current working directory.

Options:

- `--dpi` (optional integer): The resolution in dots per inch (DPI) for rendering images. The default value is 300 DPI, because this provides excellent quality when printing on A4 paper, but does not result in an excessively large output file size.
- `--batch` (optional integer): The number of pages to be included in each batch. The default value is 4, as A5 booklets printed on 80 g/m² A4 paper are easy to fold when they consist of 4 sheets (16 A5 pages).
- `--fold` (optional float): The offset in millimeters from the sheet bend. This helps to ensure the necessary distance from the bend of the sheet.
- `--shift` (optional float): The distance in millimeters by which A5 page sides will be shifted toward the nearest short side of the A4 sheet. Useful when you need to increase the distance at the fold of the sheet. Negative values can also be used.
- `--crop` (optional boolean): If set, the pages will be cropped to remove any white margins.
-- `--skip-crop` (optional string): A comma-separated list of page numbers (1-based) that should not be cropped, even if the `--crop` option is enabled.
- `--workers` (optional integer): The number of worker processes to use for parallel processing. The default value is 4.

## Examples

We have a `document.pdf` whose pages contain margins (white borders). We want to crop them, but ensure our own indents in accordance with the following rule: there must be a 5 mm margin from the edge of the page and a 20 mm margin from the fold of the sheet. The title on the first and second pages is on a white background, so we don't want to crop them. To achieve this result, we need to run the program with the following launch parameters:

```bash
pdf2a5 document.pdf --crop --fold 25 --shift -5 --skip-crop 1,2
```
