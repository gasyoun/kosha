# Changesets

## Notes on the format (kosha, H8385)

`.changeset/*.md` files accumulate release intents. On push to `main`, the
[changesets/action](https://github.com/changesets/action) workflow
(`.github/workflows/changesets.yml`) opens or refreshes a **Version Packages**
PR that runs `npx changeset version`: it bumps `ui/package.json`, writes
`ui/CHANGELOG.md`, and consumes the changeset files. Merging that PR IS the
release of the UI line.

- Only `ui/` is managed (`config.json` → `packages: ["ui"]`). The root kosha
  data release line stays on **cut-release** (`CHANGELOG.md` +
  `changelog_queue/`) — the two surfaces coexist by design (ADR-0005).
- This repo **never npm-publishes**: `ui/` is `private: true`
  (`privatePackages.version: true`, `tag: false`, publish absent from the
  workflow).

A changeset file looks like:

```md
---
"kosha-inflect-ui": patch
---

One-line description of the change for the UI changelog.
```
