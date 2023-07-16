The queries here are for testing query reconstruction. We'll load one of these queries,
run it against the test database and acquire the results. Then we'll parse the query
with the grammar, then rebuild the query from the AST. Finally we'll run the
reconstructed query against the test database and compare the results with the original
query.

The more queries we have, the better, because it proves that the reconstructor is
working as intended and has no semantic differences.
