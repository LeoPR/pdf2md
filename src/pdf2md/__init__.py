"""pdf2md — conversor PDF→Markdown CPU-first com roteamento por intent.

Núcleo CPU (pdftotext/PyMuPDF) offline e determinístico; capacidades pesadas
(marker/GPU, pix2tex, OCR, VLM) são opcionais e detectadas em runtime via
`pdf2md doctor`. CLI em `pdf2md.cli:app`.
"""

__version__ = "0.8.1"
