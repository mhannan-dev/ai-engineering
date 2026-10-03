"""Integration tests for avatar upload (stored via the uploads table)."""

import os
from io import BytesIO
from pathlib import Path

from PIL import Image


def _image(fmt: str, size=(900, 600), mode="RGB") -> bytes:
    buf = BytesIO()
    Image.new(mode, size, "red").save(buf, format=fmt)
    return buf.getvalue()


def _post(client, headers, name, data, content_type="image/png"):
    return client.post("/api/v1/users/me/avatar", headers=headers, files={"file": (name, data, content_type)})


def test_upload_converts_to_webp_and_resizes(client, auth_headers, db_session):
    res = _post(client, auth_headers, "photo.png", _image("PNG"))
    assert res.status_code == 200
    avatar = res.json()["avatar"]
    assert avatar.startswith("/uploads/avatars/") and avatar.endswith(".webp")

    served = client.get(avatar)
    assert served.status_code == 200
    img = Image.open(BytesIO(served.content))
    assert img.format == "WEBP" and max(img.size) <= 512

    [upload] = db_session.uploads.list_for_user(res.json()["id"], "avatar")
    assert (upload.original_filename, upload.content_type) == ("photo.png", "image/webp")


def test_replacing_avatar_deletes_previous_file_and_row(client, auth_headers, db_session):
    first = _post(client, auth_headers, "a.jpg", _image("JPEG"), "image/jpeg").json()["avatar"]
    second = _post(client, auth_headers, "b.webp", _image("WEBP"), "image/webp").json()
    assert client.get(first).status_code == 404
    assert len(db_session.uploads.list_for_user(second["id"], "avatar")) == 1


def test_remove_avatar(client, auth_headers, db_session):
    user_id = _post(client, auth_headers, "a.png", _image("PNG")).json()["id"]
    res = client.delete("/api/v1/users/me/avatar", headers=auth_headers)
    assert res.status_code == 200 and res.json()["avatar"] is None
    assert db_session.uploads.list_for_user(user_id) == []
    assert not any(Path(os.environ["UPLOAD_DIR"], "avatars").iterdir())


def test_disallowed_formats_rejected(client, auth_headers):
    # A GIF renamed to .png must still be rejected: format is detected from content
    assert _post(client, auth_headers, "renamed.png", _image("GIF")).status_code == 415
    assert _post(client, auth_headers, "x.bmp", _image("BMP")).status_code == 415
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>'
    assert _post(client, auth_headers, "x.svg", svg, "image/svg+xml").status_code == 415


def test_oversized_upload_rejected(client, auth_headers):
    big = b"\xff\xd8\xff" + os.urandom(2 * 1024 * 1024 + 1)
    assert _post(client, auth_headers, "big.jpg", big, "image/jpeg").status_code == 413


def test_avatar_requires_authentication(client):
    assert _post(client, {}, "a.png", _image("PNG")).status_code == 401
