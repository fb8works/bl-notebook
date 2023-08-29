from .local import BlenderLocalRepository
from .remote import BlenderRemoteRepository


class Repository:
    def __init__(self, search_path, url, apps_root, cache_dir, ext_re, strict):
        self.local = BlenderLocalRepository(search_path, strict=strict)
        self.remote = BlenderRemoteRepository(
            url=url, apps_root=apps_root, cache_dir=cache_dir, ext_re=ext_re
        )
