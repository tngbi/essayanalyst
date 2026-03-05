import sys, os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import importlib.util

# Skip tests if heavy visualization deps are not installed in the environment
if importlib.util.find_spec("wordcloud") is None or importlib.util.find_spec("pyvis") is None or importlib.util.find_spec("networkx") is None:
    pytest.skip("Skipping content visualisation tests: heavy visualization dependencies are not installed.", allow_module_level=True)

from analyst.content_visualisation import generate_wordcloud, build_knowledge_graph, render_graph
import matplotlib.pyplot as plt


def test_generate_wordcloud_returns_figure():
    fig = generate_wordcloud("this is a test text with some repeated words test test")
    assert hasattr(fig, "axes")
    assert len(fig.axes) >= 1
    plt.close(fig)


def test_render_graph_creates_file(tmp_path):
    G = build_knowledge_graph("Alice loves Bob. Bob supports Carol.")
    html = render_graph(G)
    assert os.path.exists(html)
    # cleanup
    try:
        os.remove(html)
    except Exception:
        pass
