from src.media_tagger import MediaTagger, TaggedAsset


class FakeClient:
    def upload(self, image_bytes, filename):
        assert image_bytes == b"pixels"
        assert filename == "summer_beach.jpg"
        return {"id": "img_123"}


def test_ingest_returns_search_tags_and_image_id():
    result = MediaTagger(FakeClient()).tag_asset("summer_beach.jpg", b"pixels")
    assert result == TaggedAsset("img_123", ["summer", "beach"], "summer_beach.jpg")
