import argparse
import json
import mimetypes
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv


PINATA_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
DEFAULT_METADATA_PATH = Path("others/agent/agent-metadata.json")


def get_auth_headers() -> dict[str, str]:
    jwt = os.getenv("PINATA_JWT")
    if jwt:
        return {"Authorization": f"Bearer {jwt}"}

    api_key = os.getenv("PINATA_API_KEY")
    secret_api_key = os.getenv("PINATA_SECRET_API_KEY")
    if api_key and secret_api_key:
        return {
            "pinata_api_key": api_key,
            "pinata_secret_api_key": secret_api_key,
        }

    raise SystemExit(
        "Missing Pinata credentials. Set PINATA_JWT, or both "
        "PINATA_API_KEY and PINATA_SECRET_API_KEY in .env."
    )


def get_default_image_source() -> str:
    with DEFAULT_METADATA_PATH.open("r", encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)

    image = metadata.get("image")
    if not image:
        raise SystemExit(f"No image field found in {DEFAULT_METADATA_PATH}.")

    return image


def download_url(url: str) -> Path:
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".img"
    target_path = Path(tempfile.gettempdir()) / f"pinata-upload-{uuid4()}{suffix}"
    urllib.request.urlretrieve(url, target_path)
    return target_path


def resolve_image_path(source: str) -> tuple[Path, bool]:
    if source.startswith(("http://", "https://")):
        return download_url(source), True

    image_path = Path(source).expanduser()
    if not image_path.is_absolute():
        image_path = Path.cwd() / image_path

    if not image_path.is_file():
        raise SystemExit(f"Image file not found: {image_path}")

    return image_path, False


def build_multipart_body(image_path: Path) -> tuple[bytes, str]:
    boundary = f"----pinata-boundary-{uuid4().hex}"
    content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    file_bytes = image_path.read_bytes()

    parts = [
        f"--{boundary}\r\n".encode(),
        (
            'Content-Disposition: form-data; name="file"; '
            f'filename="{image_path.name}"\r\n'
        ).encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        file_bytes,
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="pinataMetadata"\r\n',
        b"Content-Type: application/json\r\n\r\n",
        json.dumps({"name": image_path.name}).encode(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]

    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def upload_to_pinata(image_path: Path) -> dict:
    body, content_type = build_multipart_body(image_path)
    headers = {
        **get_auth_headers(),
        "Content-Type": content_type,
    }

    request = urllib.request.Request(
        PINATA_UPLOAD_URL,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Pinata upload failed: HTTP {error.code}\n{detail}") from error


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Upload an image to Pinata IPFS.")
    parser.add_argument(
        "image",
        nargs="?",
        help=(
            "Local image path or image URL. Defaults to the image field in "
            "others/agent/agent-metadata.json."
        ),
    )
    args = parser.parse_args()

    source = args.image or get_default_image_source()
    image_path, should_delete = resolve_image_path(source)

    try:
        result = upload_to_pinata(image_path)
    finally:
        if should_delete:
            image_path.unlink(missing_ok=True)

    ipfs_hash = result.get("IpfsHash")
    print(json.dumps(result, indent=2))
    if ipfs_hash:
        print(f"\nIPFS URI: ipfs://{ipfs_hash}")
        print(f"Gateway URL: https://gateway.pinata.cloud/ipfs/{ipfs_hash}")


if __name__ == "__main__":
    main()
