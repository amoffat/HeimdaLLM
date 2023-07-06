from heimdallm.bifrosts.sql import exc
from heimdallm.bifrosts.sql.sqlite.select.bifrost import Bifrost


def test_ambiguous_parse():
    query = "select * from whatever"
    grammar = Bifrost.build_grammar()
    tree = grammar.parse(query)
    trees = [tree, tree, tree]

    e = exc.AmbiguousParse(trees=trees, query=query)
    # brittle, but shows that the query is making its way into the issue link
    assert "whatever" in e.issue_link
