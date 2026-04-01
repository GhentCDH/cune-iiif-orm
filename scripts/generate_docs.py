#!/usr/bin/env python3
"""Generate HTML documentation from the cune-iiif-orm JSON-LD vocabulary."""

import json
import sys
from pathlib import Path
from html import escape


def expand_id(term_id: str, context: dict) -> str:
    """Expand a prefixed IRI like 'cune-iiif-orm:Foo' to its full IRI."""
    if ":" in term_id:
        prefix, local = term_id.split(":", 1)
        if prefix in context and not local.startswith("//"):
            return context[prefix] + local
    return term_id


def local_name(iri: str, context: dict) -> str:
    """Return the local name (fragment or last path segment) of an IRI."""
    for prefix, base in context.items():
        if isinstance(base, str) and iri.startswith(base):
            return iri[len(base):]
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.split("/")[-1]


def get_lang_value(node, key: str) -> str:
    """Get the string value of a language-tagged literal or plain string."""
    val = node.get(key)
    if val is None:
        return ""
    if isinstance(val, dict):
        return val.get("@value", "")
    return str(val)


def resolve_id(node, context: dict) -> str:
    """Resolve the full IRI of a node."""
    raw = node.get("@id", "")
    return expand_id(raw, context)


def generate_html(vocab_path: Path) -> str:
    with open(vocab_path, encoding="utf-8") as f:
        vocab = json.load(f)

    context = vocab.get("@context", {})
    graph = vocab.get("@graph", [])

    # Separate ontology metadata from terms
    ontology = next((n for n in graph if "owl:Ontology" in str(n.get("@type", ""))), {})
    classes = [n for n in graph if n.get("@type") == "rdfs:Class"]
    properties = [n for n in graph if n.get("@type") == "rdf:Property"]

    ns_iri = ontology.get("@id", "")
    label = get_lang_value(ontology, "rdfs:label") or "Vocabulary"
    description = get_lang_value(ontology, "rdfs:comment")
    creator = ontology.get("dcterms:creator", "")
    license_url = ontology.get("dcterms:license", "")
    version = ontology.get("owl:versionInfo", "")

    def term_anchor(node) -> str:
        return local_name(resolve_id(node, context), context)

    def render_iri(iri: str) -> str:
        return f'<a href="{escape(iri)}">{escape(iri)}</a>'

    def render_domain_range(node, key: str) -> str:
        val = node.get(key)
        if not val:
            return ""
        raw_id = val.get("@id", "") if isinstance(val, dict) else str(val)
        full = expand_id(raw_id, context)
        return render_iri(full)

    def render_term(node) -> str:
        anchor = term_anchor(node)
        full_iri = resolve_id(node, context)
        term_label = get_lang_value(node, "rdfs:label") or anchor
        comment = get_lang_value(node, "rdfs:comment")
        domain_html = render_domain_range(node, "rdfs:domain")
        range_html = render_domain_range(node, "rdfs:range")

        rows = ""
        rows += f"<tr><th>IRI</th><td>{render_iri(full_iri)}</td></tr>\n"
        if comment:
            rows += f"<tr><th>Description</th><td>{escape(comment)}</td></tr>\n"
        if domain_html:
            rows += f"<tr><th>Domain</th><td>{domain_html}</td></tr>\n"
        if range_html:
            rows += f"<tr><th>Range</th><td>{range_html}</td></tr>\n"

        return f"""
    <section id="{escape(anchor)}">
      <h3><a href="#{escape(anchor)}">{escape(term_label)}</a></h3>
      <table>
        {rows}
      </table>
    </section>"""

    classes_html = "\n".join(render_term(c) for c in classes)
    properties_html = "\n".join(render_term(p) for p in properties)

    license_html = (
        f'<a href="{escape(license_url)}">{escape(license_url)}</a>' if license_url else ""
    )

    jsonld_url = ns_iri + ".jsonld" if ns_iri else "ns.jsonld"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(label)}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      color: #1a1a1a;
      max-width: 900px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header {{ border-bottom: 2px solid #e1e4e8; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
    header h1 {{ margin: 0 0 0.5rem; font-size: 2rem; }}
    .meta {{ font-size: 0.9rem; color: #57606a; }}
    .meta span {{ margin-right: 1.5rem; }}
    .download {{ margin-top: 1rem; }}
    .download a {{
      display: inline-block;
      padding: 0.3rem 0.8rem;
      border: 1px solid #0969da;
      border-radius: 4px;
      font-size: 0.85rem;
    }}
    h2 {{
      font-size: 1.4rem;
      border-bottom: 1px solid #e1e4e8;
      padding-bottom: 0.4rem;
      margin-top: 2.5rem;
    }}
    section {{ margin-bottom: 2rem; }}
    section h3 {{
      font-size: 1.1rem;
      margin-bottom: 0.5rem;
      background: #f6f8fa;
      padding: 0.5rem 0.75rem;
      border-left: 3px solid #0969da;
      border-radius: 0 4px 4px 0;
    }}
    section h3 a {{ color: inherit; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
    th, td {{
      text-align: left;
      padding: 0.4rem 0.75rem;
      border-bottom: 1px solid #e1e4e8;
      vertical-align: top;
    }}
    th {{ width: 120px; color: #57606a; font-weight: 600; white-space: nowrap; }}
    td {{ word-break: break-all; }}
    .namespace-box {{
      background: #f6f8fa;
      border: 1px solid #e1e4e8;
      border-radius: 6px;
      padding: 0.75rem 1rem;
      font-family: monospace;
      font-size: 0.9rem;
      margin: 1rem 0 2rem;
    }}
    footer {{ margin-top: 3rem; font-size: 0.85rem; color: #57606a; border-top: 1px solid #e1e4e8; padding-top: 1rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(label)}</h1>
    <div class="meta">
      {"<span>Version: " + escape(version) + "</span>" if version else ""}
      {"<span>Creator: " + escape(creator) + "</span>" if creator else ""}
      {"<span>License: " + license_html + "</span>" if license_html else ""}
    </div>
    <div class="download">
      <a href="{escape(jsonld_url)}">Download JSON-LD</a>
    </div>
  </header>

  {"<p>" + escape(description) + "</p>" if description else ""}

  <h2>Namespace</h2>
  <div class="namespace-box">{escape(ns_iri + "#")}</div>

  <h2>Classes</h2>
  {classes_html if classes_html.strip() else "<p>No classes defined.</p>"}

  <h2>Properties</h2>
  {properties_html if properties_html.strip() else "<p>No properties defined.</p>"}

  <footer>
    Generated from <a href="{escape(jsonld_url)}">cune-iiif-orm.jsonld</a>.
  </footer>
</body>
</html>
"""


if __name__ == "__main__":
    vocab_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("vocabulary/cune-iiif-orm.jsonld")
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_site/ns")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    html = generate_html(vocab_file)
    output_file.write_text(html, encoding="utf-8")
    print(f"Generated {output_file}")
