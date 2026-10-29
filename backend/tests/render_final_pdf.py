# Rasterize the generated PDF for visual review; test-only dependency pypdfium2.
from pathlib import Path
import pypdfium2 as pdfium
p=Path('/app/test_reports/browser_iter5_focused/populated_report.pdf')
doc=pdfium.PdfDocument(p)
assert len(doc)==1
image=doc[0].render(scale=1.5).to_pil()
image.convert('RGB').save(p.with_suffix('.jpg'),quality=40)
print('Rendered one-page report:',p.with_suffix('.jpg'))