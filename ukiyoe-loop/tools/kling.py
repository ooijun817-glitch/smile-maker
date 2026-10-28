"""Kling の「絵から動画」を呼ぶための小さな道具。標準ライブラリだけで動く。

鍵は .env(または環境変数)から読む。コードには書かない。

仕様は Kling の公開情報をもとにしている(2026-10 時点、公式の説明書は未照合):
- 認証:アクセスキーとシークレットキーから 30 分有効の JWT(HS256)を作り、
  Authorization: Bearer で送る
- 作成:POST {base}/v1/videos/image2video → data.task_id
- 確認:GET  {base}/v1/videos/image2video/{task_id}
        → data.task_status(submitted / processing / succeed / failed)
        → data.task_result.videos[0].url
"""

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path=ROOT / ".env"):
    """.env を読んで os.environ に入れる(すでに環境変数にあるものは上書きしない)。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def config():
    load_env()
    cfg = {
        "access_key": os.environ.get("KLING_ACCESS_KEY", ""),
        "secret_key": os.environ.get("KLING_SECRET_KEY", ""),
        "base": os.environ.get("KLING_API_BASE", "https://api-singapore.klingai.com").rstrip("/"),
        "model": os.environ.get("KLING_MODEL", "kling-v2-5-turbo"),
        "mode": os.environ.get("KLING_MODE", "pro"),
    }
    return cfg


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_token(access_key: str, secret_key: str, now=None) -> str:
    """Kling 用の JWT。iss=アクセスキー、30 分有効、5 秒前から有効。"""
    now = int(now if now is not None else time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
    signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + \
        _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64url(sig)


class KlingError(RuntimeError):
    pass


class Kling:
    def __init__(self, cfg=None):
        self.cfg = cfg or config()
        if not self.cfg["access_key"] or not self.cfg["secret_key"]:
            raise KlingError(".env に KLING_ACCESS_KEY と KLING_SECRET_KEY を書いてください(.env.example 参照)")

    def _request(self, method, path, body=None):
        token = make_token(self.cfg["access_key"], self.cfg["secret_key"])
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.cfg["base"] + path,
            data=data,
            method=method,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise KlingError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from None
        if res.get("code", 0) != 0:
            raise KlingError(f"Kling がエラーを返しました: code={res.get('code')} {res.get('message')}")
        return res.get("data") or {}

    def create_image2video(self, image_b64, prompt, image_tail_b64=None, negative_prompt="",
                           duration="5", cfg_scale=0.5):
        body = {
            "model_name": self.cfg["model"],
            "mode": self.cfg["mode"],
            "duration": str(duration),
            "image": image_b64,
            "prompt": prompt,
            "cfg_scale": cfg_scale,
        }
        if image_tail_b64:
            body["image_tail"] = image_tail_b64
        if negative_prompt:
            body["negative_prompt"] = negative_prompt
        data = self._request("POST", "/v1/videos/image2video", body)
        if "task_id" not in data:
            raise KlingError(f"task_id が返ってきませんでした: {data}")
        return data["task_id"]

    def get_task(self, task_id):
        return self._request("GET", f"/v1/videos/image2video/{task_id}")

    def wait(self, task_id, interval=10, timeout=30 * 60, log=print):
        start = time.time()
        while True:
            data = self.get_task(task_id)
            status = data.get("task_status")
            if status == "succeed":
                videos = (data.get("task_result") or {}).get("videos") or []
                if not videos:
                    raise KlingError(f"完成したのに動画がありません: {data}")
                return videos[0]
            if status == "failed":
                raise KlingError(f"生成に失敗しました: {data.get('task_status_msg')}")
            if time.time() - start > timeout:
                raise KlingError(f"{timeout // 60} 分待っても終わりませんでした(task_id={task_id})")
            log(f"  …{status}({int(time.time() - start)} 秒経過)")
            time.sleep(interval)


def download(url, dest):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return dest
