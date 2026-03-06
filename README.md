# Open Handbook: Digital Literacy

This repository is for the book on Digital Literacy

## Build

### Prerequisites
- [Quarto](https://quarto.org/)
- A LaTeX distribution:
  - TinyTex: `quarto install tinytex`
- Python packages: 
  - `pip install pyyaml pypdf reportlab`

### Render PDF
```bash
quarto render
```

Output will appear in `_book/`.

**Note:** The rendered PDF will not be version-controlled on GitHub; it will be uploaded as a binary with each release.