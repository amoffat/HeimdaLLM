from urllib.parse import quote


def _dict_to_qs(params):
    """Converts a dict to a query string, with values url-encoded"""
    qs = []
    for k, v in params.items():
        qs.append(f"{quote(k)}={quote(str(v))}")
    return "&".join(qs)


def make_issue_link(*, title: str, body: str, labels: list[str] = []) -> str:
    """Makes a generic GH issue"""
    url = "https://github.com/amoffat/HeimdaLLM/issues/new"
    params = {
        "title": title,
        "body": body,
        "labels": ",".join(labels),
    }
    return f"{url}?{_dict_to_qs(params)}"


def make_ambiguous_parse_issue(query, trees):
    """Makes a GH issue for an ambiguous parse"""

    def fmt_tree(i, tree):
        return f"""
## Tree {i}
```\n{tree.pretty()}```
""".strip()

    nice_trees = "\n\n".join(fmt_tree(i, tree) for i, tree in enumerate(trees))
    body = f"""# Query

```sql
{query}
```

# Parse trees
{nice_trees}
""".strip()
    return make_issue_link(
        title="Ambiguous parse",
        body=body,
        labels=["bug", "ambiguous parse"],
    )
