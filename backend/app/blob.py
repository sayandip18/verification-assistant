import uuid
from functools import lru_cache
from pathlib import Path

from app.config import settings


def make_blob_key(application_id: uuid.UUID, document_type: str, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"applications/{application_id}/{document_type}/{uuid.uuid4()}_{safe_name}"


def ensure_bucket() -> None:
    if settings.blob_backend == "s3":
        _s3_ensure_bucket()
        return
    Path(settings.blob_local_dir).mkdir(parents=True, exist_ok=True)


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    if settings.blob_backend == "s3":
        _s3_put(key, data, content_type)
        return
    path = Path(settings.blob_local_dir) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def get_bytes(key: str) -> bytes:
    if settings.blob_backend == "s3":
        response = _cached_s3().get_object(Bucket=settings.s3_bucket, Key=key)
        return response["Body"].read()
    path = Path(settings.blob_local_dir) / key
    return path.read_bytes()


def _s3_client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


@lru_cache(maxsize=1)
def _cached_s3():
    return _s3_client()


def _s3_ensure_bucket() -> None:
    from botocore.exceptions import ClientError

    client = _cached_s3()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.s3_bucket)


def _s3_put(key: str, data: bytes, content_type: str) -> None:
    _cached_s3().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
