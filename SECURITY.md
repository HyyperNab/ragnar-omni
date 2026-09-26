# SECURITY

## Reporting

Vulnerabilities in this engine (especially: any path that could emit a
QUARANTINED/unverified citation, any bypass of the Omega Lock, any injection
surface in the API) → open a private security advisory on the repo or contact
the maintainer directly. Please do not open public issues for exploitable
findings.

## Threat model (what this engine must survive)

| Threat | Defense |
|---|---|
| Poisoned research dossiers fed into the KB | CitationTrust tiers; quarantined entries structurally unemittable |
| Fake precedent in generated output | court docs emit CONFIRMED-only; statute-first architecture survives deletion of any case |
| Omega Lock replay | nonce set survives re-engagement; timing-safe key comparison; rotation invalidates (fail-closed) |
| Tripwire misfires (negations) | sentence-scoped negation guards; contract-tested |
| Secrets leakage | env-only; git/docker-ignored; image bakes no key; API key gate fail-closed |
| Tampering with the decision record | hash-chained audit trail; `verify()` re-computes the chain |
| Container escape surface | non-root, read-only rootfs, no-new-privileges, resource limits |
| Overconfident output (the deepest) | every proposition priced; load-bearing thresholds; the audit trail logs every gate |

## Hardening checklist for production

1. `RAGNAR_OMEGA_KEY`: 32+ random bytes from a real secret store — never
   .env in a shared environment, never a flag, never committed.
2. `RAGNAR_API_KEY`: set it if the API is reachable by anything you don't
   fully trust; front with TLS.
3. Keep the image pinned; consider hash-pinning the base digest (named cover
   in SPOF_ANALYSIS.md §I7).
4. Reverify the citation registry on the calendar date; `/health` will tell
   you when it's due.
5. The in-binary suite (`ragnar --test`) is your runtime integrity check —
   run it from cron.
