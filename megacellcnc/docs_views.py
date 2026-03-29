"""
Handbuch (MegaCell Manual-DE.md): HTML-Ansicht und PDF (WeasyPrint).
"""
from pathlib import Path

import markdown
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def _manual_path():
    return Path(settings.BASE_DIR) / 'docs' / 'MegaCell Manual-DE.md'


def render_manual_markdown():
    """Gibt (body_html, toc_html) oder (None, None) bei fehlender Datei zurück."""
    path = _manual_path()
    if not path.is_file():
        return None, None
    text = path.read_text(encoding='utf-8')
    md = markdown.Markdown(
        extensions=[
            'tables',
            'fenced_code',
            'nl2br',
            'toc',
        ],
        extension_configs={
            'toc': {
                'title': 'Inhaltsverzeichnis',
                'toc_depth': '2-3',
                'anchorlink': True,
            },
        },
    )
    body_html = md.convert(text)
    toc_html = getattr(md, 'toc', '') or ''
    return body_html, toc_html


def manual(request):
    body_html, toc_html = render_manual_markdown()
    if body_html is None:
        return render(
            request,
            'megacellcnc/manual_missing.html',
            {'page_title': 'Handbuch'},
        )
    return render(
        request,
        'megacellcnc/manual.html',
        {
            'page_title': 'Handbuch',
            'manual_body': body_html,
            'manual_toc': toc_html,
        },
    )


def manual_pdf(request):
    try:
        from weasyprint import CSS, HTML
    except ImportError:
        return HttpResponse(
            'WeasyPrint ist nicht installiert. PDF-Export nicht verfügbar.',
            status=503,
            content_type='text/plain; charset=utf-8',
        )

    body_html, _ = render_manual_markdown()
    if body_html is None:
        return HttpResponse(
            'Handbuch-Datei nicht gefunden.',
            status=404,
            content_type='text/plain; charset=utf-8',
        )

    html_str = render_to_string(
        'megacellcnc/manual_pdf.html',
        {
            'body_html': body_html,
            'title': 'Giga CN – Benutzerhandbuch',
        },
        request=request,
    )

    css_path = Path(settings.BASE_DIR) / 'static' / 'megacellcnc' / 'css' / 'manual_pdf.css'
    stylesheets = []
    if css_path.is_file():
        stylesheets.append(CSS(filename=str(css_path)))

    base_url = request.build_absolute_uri('/')
    pdf_bytes = HTML(string=html_str, base_url=base_url).write_pdf(stylesheets=stylesheets)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Giga-CN-Benutzerhandbuch.pdf"'
    return response
