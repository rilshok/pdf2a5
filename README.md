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
3. Install the module project directory by `pip install -e .`

## Usage

The command-line interface allows you to easily convert PDF files into A5 booklets. Here's how to use it:

```bash
pdf2a5 SOURCE_PDF [--dest DESTINATION_DIRECTORY] [--dpi DPI] [--batch BATCH_SIZE]
```

- `--source` `SOURCE_PDF`: The path to the source PDF file you want to convert.
- `--dest` `DESTINATION_DIRECTORY` (optional): The directory where the converted PDF booklets will be saved. If not provided, the tool will use the source PDF's directory.
- `--dpi` `DPI` (optional): The resolution in dots per inch (DPI) for rendering images. The default is 120 DPI.
- `--batch` `BATCH_SIZE` (optional): The number of pages to include in each batch. The default is 5
