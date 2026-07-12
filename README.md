# chatmail-relays-mirror

An **automated, unattended mirror** of the public chatmail relay list at
<https://chatmail.at/relays>, for machine consumption.

A scheduled GitHub Action refreshes the snapshot **daily** (and on manual
dispatch). Nothing here is curated, added, removed, or endorsed — the
workflow fetches the page, mechanically extracts the relay hostnames, and
publishes the result. **Report issues with the list's content to the
[chatmail project](https://chatmail.at), not to this repo.** This repo only
handles mirroring machinery.

## Consuming the data

The snapshot lives on the [`data`](../../tree/data) branch as a **single
force-pushed commit** — no history, the branch simply is the current
snapshot. It contains:

- `relays.html` — the fetched page, byte-for-byte verbatim
- `relays.json` — mechanically extracted from it:

```json
{
  "source": "https://chatmail.at/relays",
  "fetchedAt": "2026-07-12T03:37:00Z",
  "relays": [
    { "host": "some.relay.example" }
  ]
}
```

`host` is a validated bare DNS hostname, in page order, deduplicated. The
`source`, `fetchedAt`, and `relays[].host` fields are stable; optional
per-relay fields may appear later — ignore unknown fields.

Fetch it from:

```
https://raw.githubusercontent.com/experintellia/chatmail-relays-mirror/refs/heads/data/relays.json
```

`raw.githubusercontent.com` serves with CORS `Access-Control-Allow-Origin: *`,
so this works directly from browser apps.

If a run fails (page unreachable, layout drift, empty parse result) nothing
is pushed and the last good snapshot stays published.

## License

The mirroring machinery in this repo is released under the
[Unlicense](LICENSE). The mirrored page content (`relays.html` and data
derived from it on the `data` branch) remains the chatmail project's.
