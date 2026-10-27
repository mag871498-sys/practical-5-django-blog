"""Export a read-only SQLite viewer for the blog table, without account secrets."""

import argparse
import html
import sqlite3
from pathlib import Path


def escape(value):
    return html.escape("" if value is None else str(value))


def timestamp(value):
    date, _, time = str(value).partition(" ")
    return f"<span>{escape(date)}</span><small>{escape(time)}</small>"


def render(database, output):
    # mode=ro rejects writes at the SQLite connection level.
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        posts = connection.execute(
            "SELECT p.id, p.title, p.slug, p.status, p.publish, p.created, p.updated, "
            "COALESCE(NULLIF(u.first_name, ''), u.username) AS author "
            "FROM blog_post AS p JOIN auth_user AS u ON u.id = p.author_id ORDER BY p.id"
        ).fetchall()
        columns = connection.execute("PRAGMA table_info('blog_post')").fetchall()
        foreign_keys = connection.execute("PRAGMA foreign_key_list('blog_post')").fetchall()
        indexes = connection.execute("PRAGMA index_list('blog_post')").fetchall()
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='blog_post'"
        ).fetchone()["sql"]

    data_rows = "".join(
        f"<tr><td class='id'>{p['id']}</td>"
        f"<td class='title'><strong>{escape(p['title'])}</strong><code>{escape(p['slug'])}</code></td>"
        f"<td>{escape(p['author'])}</td><td><span class='status'>{escape(p['status'])}</span></td>"
        f"<td class='date'>{timestamp(p['publish'])}</td>"
        f"<td class='date'><label>created</label>{timestamp(p['created'])}"
        f"<label>updated</label>{timestamp(p['updated'])}</td></tr>"
        for p in posts
    )
    schema_rows = "".join(
        f"<tr><td>{c['cid']}</td><td><code>{escape(c['name'])}</code></td>"
        f"<td>{escape(c['type'])}</td><td>{'YES' if c['notnull'] else 'NO'}</td>"
        f"<td>{'PRIMARY KEY' if c['pk'] else '—'}</td></tr>" for c in columns
    )
    foreign_key_text = ", ".join(
        f"{f['from']} → {f['table']}.{f['to']}" for f in foreign_keys
    )
    index_text = ", ".join(i["name"] for i in indexes)
    document = """<!doctype html>
<html lang="uk"><head><meta charset="utf-8"><title>SQLite · blog_post</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f6f8;color:#20252d;font:18px Arial,sans-serif}
header{background:#202a37;color:white;padding:27px 40px;display:flex;align-items:center;justify-content:space-between}
header strong{font-size:25px}header span{color:#cbd7e4}main{padding:28px 40px 34px}h1{font-size:26px;margin:0 0 20px}
.tools{display:flex;align-items:center;gap:25px;margin-bottom:22px}.tools span{margin-left:auto;color:#526174}
button{font:inherit;border:0;background:none;padding:12px 2px;color:#637181;cursor:pointer;border-bottom:3px solid transparent}
button.active{color:#185898;border-bottom-color:#185898;font-weight:bold}.panel{display:none}.panel.active{display:block}
table{border-collapse:collapse;width:100%;background:white;border:1px solid #ccd2d9;table-layout:fixed}
th{text-align:left;background:#e9edf2;font-size:16px;letter-spacing:.02em}td,th{padding:16px 14px;border-bottom:1px solid #d8dde3;vertical-align:top;overflow-wrap:anywhere}
td{line-height:1.45}td strong{display:block;font-weight:600}code{font:15px Consolas,monospace;color:#435366}
.title code{display:block;margin-top:10px}small{display:block;font:13px Consolas,monospace;color:#586577;margin-top:3px}
label{display:block;font:12px Consolas,monospace;color:#6d7784;margin-bottom:3px}.date label:not(:first-child){margin-top:13px}
.date span{font:16px Consolas,monospace}.status{display:inline-block;padding:3px 8px;border:1px solid #c5cfd9;background:#f2f5f8;font:15px Consolas,monospace}
.note{color:#647080;font:14px Consolas,monospace;margin:17px 0 0}.schema{max-width:900px}.schema td,.schema th{padding:12px 15px}
.relations{font-size:15px;color:#48586b;margin:17px 0 0}details{margin-top:20px;font-size:15px}pre{white-space:pre-wrap;font:13px Consolas,monospace}
</style></head><body>
<header><strong>SQLite Viewer</strong><span>db.sqlite3 · Read only</span></header>
<main><h1>blog_post</h1><div class="tools"><button class="active" data-tab="data">Дані</button><button data-tab="schema">Схема</button><span>ROWS_COUNT рядки</span></div>
<section class="panel active" id="data"><table><colgroup><col style="width:5%"><col style="width:29%"><col style="width:9%"><col style="width:8%"><col style="width:22%"><col style="width:27%"></colgroup>
<thead><tr><th>ID</th><th>title / slug</th><th>author</th><th>status</th><th>publish</th><th>created / updated</th></tr></thead><tbody>DATA_ROWS</tbody></table>
<p class="note">SQLite · mode=ro · blog_post · ORDER BY id</p></section>
<section class="panel" id="schema"><table class="schema"><colgroup><col style="width:8%"><col style="width:25%"><col style="width:27%"><col style="width:18%"><col style="width:22%"></colgroup><thead><tr><th>#</th><th>Column</th><th>Type</th><th>NOT NULL</th><th>Key</th></tr></thead><tbody>SCHEMA_ROWS</tbody></table>
<p class="relations"><strong>Foreign key:</strong> FOREIGN_KEYS</p><p class="relations"><strong>Indexes:</strong> INDEXES</p><details><summary>CREATE TABLE</summary><pre>CREATE_SQL</pre></details></section>
</main><script>
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
document.querySelectorAll('[data-tab],.panel').forEach(el=>el.classList.remove('active'));
button.classList.add('active');document.getElementById(button.dataset.tab).classList.add('active');
}));</script></body></html>"""
    replacements = {
        "ROWS_COUNT": str(len(posts)), "DATA_ROWS": data_rows,
        "SCHEMA_ROWS": schema_rows, "FOREIGN_KEYS": escape(foreign_key_text),
        "INDEXES": escape(index_text), "CREATE_SQL": escape(schema),
    }
    for token, value in replacements.items():
        document = document.replace(token, value)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(f"Read-only SQLite: blog_post, {len(posts)} rows, {len(columns)} columns.")
    print(f"Viewer: {output.name}")


if __name__ == "__main__":
    project = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=project / "db.sqlite3")
    parser.add_argument("--output", type=Path, default=project / "reports/tmp/database-viewer.html")
    arguments = parser.parse_args()
    render(arguments.database, arguments.output)
