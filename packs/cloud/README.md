# Category: cloud

Packs defining **cloud-provider standards**.

- [`aws`](aws/) — identity/least-privilege, encryption at rest, tagging/cost governance.
- [`azure`](azure/) — identity/least-privilege, encryption at rest, tagging/cost governance.

> **Note:** aSPARK Core has no `cloud` lens yet, so cloud packs currently apply
> as plain constitution constraints (see the README's "gaps" note). A `cloud`
> lens is a tracked follow-up.

> **Flat-id rule:** the category is metadata only, never part of the import id.
> ✅ `aspark:aws`  ❌ `aspark:cloud/aws`

See [`../README.md`](../README.md) for pack anatomy and conventions.
