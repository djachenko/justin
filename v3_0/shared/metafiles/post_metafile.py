from pathlib import Path

from v3_0.shared.metafiles.metafile import Metafile


class PostMetafile(Metafile):
    def __init__(self, path: Path, post_id: int) -> None:
        super().__init__()

        self.path = path
        self.post_id = post_id

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "id": self.post_id
        }

    @classmethod
    def from_dict(cls, json: dict) -> 'PostMetafile':
        post_id = json["id"]
        path = Path(json["path"])

        return PostMetafile(path, post_id)
