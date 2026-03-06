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

## Contribute

If you wish to contribute to this book, please check out our [Authors Guidelines for detailed instructions](https://openhandbook.org/contribute/).

## Current List of Chapters

Below is the current list of chapters. Note that many sections may be empty as the book is still evolving, providing an opportunity for you to contribute.


```yaml
chapters:
    - index.qmd
    - front-matter/license.qmd
    - front-matter/disclaimers.qmd
    - front-matter/printing.qmd
    - front-matter/contribute.qmd
    - front-matter/preface.qmd
    - part: "Understanding the Digital World"
      chapters: 
        - chapters/part1/what-is-digital-literacy.qmd
        - chapters/part1/types-of-digital-devices.qmd
    - part: "Basic Digital Skills"
      chapters:
        - chapters/part2/operating-systems-and-file-management.qmd
        - chapters/part2/using-the-internet.qmd
        - chapters/part2/communication-online.qmd
    - part: "Finding and Evaluating Information"
      chapters:
        - chapters/part3/searching-for-reliable-information.qmd
        - chapters/part3/misinformation-and-fake-news.qmd
        - chapters/part3/understanding-digital-media.qmd
    - part: "Online Safety and Privacy"
      chapters:
        - chapters/part4/protecting-your-personal-information.qmd
        - chapters/part4/passwords-and-account-security.qmd
        - chapters/part4/protecting-your-personal-information.qmd
    - part: "Digital Citizenship"
      chapters:
        - chapters/part5/responsible-behavior-online.qmd
        - chapters/part5/digital-footprints.qmd
        - chapters/part5/copyright-and-creative -commons.qmd

    - part: "Creating Digital Content"
      chapters:
        - chapters/part6/writing-and-publishing-online.qmd
        - chapters/part6/working-with-digital-media.qmd
        - chapters/part6/collaboration-in-the-digital-world.qmd
    - part: "Digital Skills for Work and Learning"
      chapters:
        - chapters/part7/productivity-tools.qmd
        - chapters/part7/using-technology-for-lifelong-learning.qmd
    - part: "The Future of the Digital World"
      chapters:
        - chapters/part8/artificial-intelligence-and-automation.qmd
        - chapters/part8/ethical-use-of-technology.qmd
        - chapters/part8/staying-digitally-literate.qmd
```