from __future__ import annotations

import tempfile
from typing import List, Tuple

# All heavy/optional dependencies are imported lazily so that the module can be
# imported even when optional packages are not installed.
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            try:
                _nlp = spacy.load("en_core_web_sm")
            except OSError:
                import subprocess, sys
                subprocess.check_call(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = None
    return _nlp


def generate_wordcloud(text: str):
    try:
        from wordcloud import WordCloud, STOPWORDS
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "wordcloud and/or matplotlib are not installed. "
            "Run: pip install wordcloud matplotlib"
        ) from exc

    stopwords = set(STOPWORDS)

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        stopwords=stopwords,
        colormap="viridis",
    ).generate(text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")

    return fig


def extract_relations(text: str) -> List[Tuple[str, str, str]]:
    nlp = _get_nlp()
    if nlp is None:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not available. "
            "Run: python -m spacy download en_core_web_sm"
        )

    doc = nlp(text)

    relations = []
    for token in doc:
        if token.dep_ == "ROOT":
            subject = None
            obj = None
            for child in token.children:
                if child.dep_ in ["nsubj", "nsubjpass"]:
                    subject = child.text
                if child.dep_ in ["dobj", "attr", "pobj"]:
                    obj = child.text
            if subject and obj:
                relations.append((subject, token.text, obj))

    return relations


def build_knowledge_graph(text: str):
    try:
        import networkx as nx
    except ImportError as exc:
        raise RuntimeError("networkx is not installed. Run: pip install networkx") from exc

    relations = extract_relations(text)

    G = nx.DiGraph()
    for subj, verb, obj in relations:
        G.add_node(subj)
        G.add_node(obj)
        G.add_edge(subj, obj, label=verb)
    return G


def render_graph(G) -> str:
    try:
        from pyvis.network import Network
    except ImportError as exc:
        raise RuntimeError("pyvis is not installed. Run: pip install pyvis") from exc

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#000000",
        directed=True,
    )

    for node in G.nodes():
        net.add_node(node, label=node)

    for source, target, data in G.edges(data=True):
        net.add_edge(source, target, label=data.get("label", ""))

    import atexit, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    # Schedule cleanup of the temp file when the Python process exits
    atexit.register(lambda p=tmp.name: os.unlink(p) if os.path.exists(p) else None)
    net.save_graph(tmp.name)
    return tmp.name
