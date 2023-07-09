import pytest


def dialects(*dialects):
    def map_dialect(d):
        mod = __import__(f"heimdallm.bifrosts.sql.{d}.select.bifrost")
        bifrost = getattr(mod.bifrosts.sql, d).select.bifrost.Bifrost
        bifrost.dialect = d
        return bifrost

    return pytest.mark.parametrize(
        "Bifrost",
        [map_dialect(d) for d in dialects],
        ids=dialects,
    )
