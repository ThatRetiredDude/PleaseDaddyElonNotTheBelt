"""pde.credutil redaction (no key material in assertions)."""

from pde import credutil


def test_redact_masks_secrets() -> None:
    d = {
        "consumer_key": "ak12345",
        "consumer_secret": "s3cr3t0",
        "access_token": "tok" * 20,
        "access_token_secret": "ats",
        "bearer_token": "bearer" * 5,
        "ai_token": "aiz",
        "ai_model": "m",
        "x_username": "u",
    }
    r = credutil.redact_credential_map(d)
    assert str(r["consumer_key"]) == "(…)2345"
    assert "s3cr3t" not in str(r["consumer_secret"])
    assert str(r["ai_model"]) == "m" and r["x_username"] == "u"


def test_support_bundle_mentions_python() -> None:
    t = credutil.support_bundle_text()
    assert "Python" in t
