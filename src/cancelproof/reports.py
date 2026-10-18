"""Inert portable reports: escaped HTML, no scripts, no external resources."""
import html
import json
from pathlib import Path


def write_reports(report, output):
    folder=Path(output)
    folder.mkdir(parents=True, exist_ok=False)
    text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)
    (folder/'report.json').write_text(text+'\n',encoding='utf-8')
    title=html.escape(str(report.get('verdict','UNKNOWN')))
    body=html.escape(text)
    (folder/'report.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
        '<title>CancelProof report</title><style>body{font:16px system-ui;max-width:1000px;margin:3em auto;padding:1em}'
        'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f8;padding:1em}</style>'
        '<h1>CancelProof: '+title+'</h1><p>Bounded named-checkpoint test. Not a race-freedom proof.</p><pre>'+body+'</pre></html>',
        encoding='utf-8')
    # Indented code is inert in Markdown, including raw HTML and backtick fences.
    (folder/'report.md').write_text('# CancelProof: '+title+'\n\n'+
        '\n'.join('    '+line for line in text.splitlines())+'\n',encoding='utf-8')
    runs=report.get('runs',[report])
    replay={'schema_version':1,'scenario':report.get('scenario'), 'runs':[
        {k:r.get(k) for k in ('plan','limits','source_sha256')} for r in runs]}
    (folder/'replay.json').write_text(json.dumps(replay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return folder
