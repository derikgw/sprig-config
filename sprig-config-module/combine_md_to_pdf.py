#!/usr/bin/env python3
"""
Combine all markdown files in the repository into a single PDF.
"""
import os
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from io import StringIO

# Directories to exclude from search
EXCLUDE_DIRS = {'.venv', '.pytest_cache', 'node_modules', '.git', '__pycache__', 'dist', 'build'}

def find_markdown_files(root_dir):
    """Find all markdown files, excluding specified directories."""
    md_files = []
    root_path = Path(root_dir)

    for md_file in root_path.rglob('*.md'):
        # Check if any parent directory is in exclude list
        if any(excluded in md_file.parts for excluded in EXCLUDE_DIRS):
            continue
        md_files.append(md_file)

    # Sort files for consistent ordering
    md_files.sort()
    return md_files

def combine_markdown_files(md_files):
    """Combine all markdown files into a single markdown string."""
    combined = StringIO()

    for i, md_file in enumerate(md_files):
        if i > 0:
            combined.write('\n\n---\n\n')  # Page break separator

        # Add file header
        relative_path = md_file.relative_to(Path.cwd().parent if 'sprig-config-module' in str(Path.cwd()) else Path.cwd())
        combined.write(f'# File: {relative_path}\n\n')

        # Read and add file content
        try:
            content = md_file.read_text(encoding='utf-8')
            combined.write(content)
            combined.write('\n')
        except Exception as e:
            combined.write(f'*Error reading file: {e}*\n')

    return combined.getvalue()

def convert_to_pdf(markdown_content, output_pdf):
    """Convert markdown content to PDF."""
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'extra',
        'codehilite',
        'toc',
        'tables',
        'fenced_code'
    ])
    html_content = md.convert(markdown_content)

    # Create full HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>SprigConfig Documentation</title>
        <style>
            @page {{
                size: letter;
                margin: 1in;
                @bottom-right {{
                    content: counter(page);
                }}
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                page-break-before: auto;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 8px;
                margin-top: 25px;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 20px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: "Monaco", "Menlo", "Courier New", monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 16px;
                border-radius: 6px;
                overflow-x: auto;
                border: 1px solid #e1e4e8;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f6f8fa;
                font-weight: bold;
            }}
            hr {{
                border: none;
                border-top: 3px double #bdc3c7;
                margin: 40px 0;
                page-break-after: always;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #7f8c8d;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            ul, ol {{
                margin-left: 20px;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    HTML(string=full_html).write_pdf(output_pdf)

def main():
    """Main function."""
    print("Finding markdown files...")

    # Start from project root (parent of sprig-config-module)
    project_root = Path.cwd().parent if 'sprig-config-module' in str(Path.cwd()) else Path.cwd()
    md_files = find_markdown_files(project_root)

    print(f"Found {len(md_files)} markdown files")

    print("Combining markdown files...")
    combined_md = combine_markdown_files(md_files)

    # Save combined markdown for reference
    combined_md_path = project_root / 'combined_documentation.md'
    combined_md_path.write_text(combined_md, encoding='utf-8')
    print(f"Saved combined markdown to: {combined_md_path}")

    print("Converting to PDF...")
    output_pdf = project_root / 'sprig_config_documentation.pdf'
    convert_to_pdf(combined_md, str(output_pdf))

    print(f"✓ PDF created: {output_pdf}")
    print(f"  - Total files included: {len(md_files)}")

if __name__ == '__main__':
    main()
