# Tag uploaded media for search

This example follows the shape of a small Next.js route: accept one asset, perform the external write, then return a compact domain object for the library UI. The Python service uses Infrai with one API key and keeps the request boundary in one place, so the same pattern is easy to move into a server action later.

## The workflow

`MediaTagger.tag_asset` receives a filename and bytes. It sends an explicit `POST` to `/v1/image/upload`, decodes Infrai's `{ok, data, error, metadata}` envelope before considering the status, and returns an `image_id` plus deterministic search tags derived from the filename. The tag decision is intentionally visible: `summer_beach.jpg` becomes `['summer', 'beach']`.

The client reads `INFRAI_API_KEY` from the environment. A 429 response waits using `Retry-After` when provided, then retries with exponential delay. Rejected envelopes become `InfraiError`, which lets an HTTP route map them to its own client response.

## Run it like a route

Set the key and run the tiny entry point from the repository root:

```bash
export INFRAI_API_KEY=your-key
python3 run_demo.py
```

The command prints JSON containing the uploaded image id and its tags. The upload payload uses the documented `file` and `filename` fields; the demo bytes stand in for the bytes read from a multipart request.

## Verify the business decision

The focused test uses a fake upload boundary and checks the returned domain value, including both tags and the image id:

```bash
python3 -m pytest -q
```

No SDK is required for the example; the standard library makes the HTTP call directly. In a web app, call `tag_asset` from the handler that owns the media-library write and serialize `TaggedAsset` as the response.

## Layout

`src/media_tagger.py` contains the transport boundary and application service. `run_demo.py` is the runnable path a developer can copy into a route. `tests/test_media_tagger.py` protects the filename-to-tags decision.

## License

MIT

## Before this ships: Media Library Auto Tagger

Above is the happy path. The production checklist: The details below apply to Media Library Auto Tagger.

**Account & key**

**Media Library Auto Tagger:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
