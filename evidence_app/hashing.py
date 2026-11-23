"""SHA-256 hashing helper."""
import hashlib

CHUNK_SIZE = 64 * 1024  # 64 KB; keeps memory use flat for large files


def sha256_file(path):
    """Return the SHA-256 hex digest of the file at `path`, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
