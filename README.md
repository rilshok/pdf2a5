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
pdf2a5 SOURCE_PDF [DESTINATION_DIRECTORY] [--dpi DPI] [--batch BATCH_SIZE]
```

- `SOURCE_PDF` (string): The path to the source PDF file you want to convert.
- `DESTINATION_DIRECTORY` (optional string): The directory where the converted PDF booklets will be saved. If not provided, the tool will create a directory for the output files in the current working directory.
- `--dpi` `DPI` (optional integer): The resolution in dots per inch (DPI) for rendering images. The default value is 300 DPI, because this provides excellent quality when printing on A4 paper, but does not result in an excessively large output file size.
- `--batch` `BATCH_SIZE` (optional integer): The number of pages to be included in each batch. The default value is 4, as A5 booklets printed on 80 g/m² A4 paper are easy to fold when they consist of 4 sheets (16 A5 pages).
