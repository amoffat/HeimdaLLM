import pytest


def dialects(*dialects, bifrost=True, envelope=False):
    dialects = dialects or ("sqlite", "mysql")

    def map_dialect(d):
        args = []

        if bifrost:
            bf_mod = __import__(f"heimdallm.bifrosts.sql.{d}.select.bifrost")
            bifrost_cls = getattr(bf_mod.bifrosts.sql, d).select.bifrost.Bifrost
            bifrost_cls.dialect = d
            args.append(bifrost_cls)

        if envelope:
            env_mod = __import__(f"heimdallm.bifrosts.sql.{d}.select.envelope")
            envelope_cls = getattr(
                env_mod.bifrosts.sql, d
            ).select.envelope.PromptEnvelope
            envelope_cls.dialect = d
            args.append(envelope_cls)

        if len(args) == 1:
            return args[0]
        return args

    args = []
    if bifrost:
        args.append("Bifrost")
    if envelope:
        args.append("PromptEnvelope")

    return pytest.mark.parametrize(
        ",".join(args),
        [map_dialect(d) for d in dialects],
        ids=dialects,
    )
