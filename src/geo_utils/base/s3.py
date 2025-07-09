import os
import hashlib
import boto3
from urllib.parse import urlparse
from botocore.exceptions import ClientError, NoCredentialsError
from tempfile import tempdir
from .log import Logger
from . import fsys


_USE_EXCEPTIONS: bool = True


def is_s3(filename: str | None) -> bool:
    """Check if a given filename refers to an S3 path.

    Args:
        filename (str | None): The path or URI to check.

    Returns:
        bool: True if the path is an S3 URI, False otherwise.
    """
    return (
        filename
        and isinstance(filename, str)
        and (filename.startswith("s3:/") or filename.startswith("/vsis3/"))
    )
    
    
def is_url(filename: str | None) -> bool:
    """Check if the input string is a valid HTTP or HTTPS URL.

    Args:
        filename (str | None): The URL string to check.

    Returns:
        bool: True if it is a URL, False otherwise.
    """
    return (
        filename 
        and isinstance(filename, str) 
        and (filename.startswith("http://") or filename.startswith("https://"))
    )


def get_bucket_name_key(uri: str | None) -> tuple[str | None, str | None]:
    """Extract the S3 bucket name and key from a given URI.

    Args:
        uri (str | None): The S3 URI to parse.

    Returns:
        tuple[str | None, str | None]: A tuple containing the bucket name and the key.
    """
    bucket_name, key_name = None, None
    if not uri:
        pass
    elif uri.startswith("s3://"):
        _, _, bucket_name, key_name = uri.split("/", 3)
    elif uri.startswith("s3:/"):
        _, bucket_name, key_name = uri.split("/", 2)
    elif uri.startswith("/vsis3/"):
        _, _, bucket_name, key_name = uri.split("/", 3)
    elif uri.startswith("https://s3.amazonaws.com/"):
        _, _, bucket_name, key_name = uri.split("/", 3)
    else:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid S3 URI: {uri}")
        bucket_name, key_name = None, uri
    return bucket_name, key_name


def etag(filename: str, client=None, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Compute the MD5 ETag of a file, handling both local files and S3 URIs.

    Args:
        filename (str): The local file path or S3 URI.
        client: Optional boto3 S3 client instance.
        chunk_size (int): Size in bytes to chunk the file for multipart hashing.

    Returns:
        str: The computed ETag or empty string if computation fails.
    """
    if filename and os.path.isfile(filename):
        md5 = []
        with open(filename, "rb") as fp:
            while True:
                data = fp.read(chunk_size)
                if not data:
                    break
                md5.append(hashlib.md5(data))
        if len(md5) == 1:
            return f"{md5[0].hexdigest()}"
        digests = b"".join(m.digest() for m in md5)
        digests_md5 = hashlib.md5(digests)
        return f"{digests_md5.hexdigest()}-{len(md5)}"

    elif filename and is_s3(filename):
        uri = filename
        ETag = ""
        try:
            bucket_name, key_name = get_bucket_name_key(uri)
            if bucket_name and key_name:
                client = get_client(client)
                ETag = client.head_object(Bucket=bucket_name, Key=key_name)["ETag"][1:-1]
        except ClientError as ex:
            ETag = ""
        except NoCredentialsError as ex:
            Logger.debug(ex)
            ETag = ""
        return ETag
    else:
        if _USE_EXCEPTIONS:
            raise ValueError(f"Invalid file or S3 URI: {filename}")
        return ""


def get_client(client=None):
    """Return a boto3 S3 client. If a client is passed, return it directly.

    Args:
        client: Existing boto3 client or None.

    Returns:
        boto3.client: An S3 client instance.
    """
    return client if client else boto3.client("s3", region_name="us-east-1")


def tempname4S3(uri: str | None) -> str:
    """Generate a temporary local file path that maps to a given S3 URI.

    Args:
        uri (str | None): The S3 URI.

    Returns:
        str: A temporary local path corresponding to the S3 URI.
    """
    dest_folder = fsys.tempdir("s3")
    uri = uri if uri else ""
    if uri.startswith("s3://"):
        tmp = uri.replace("s3://", dest_folder + "/")
    if uri.startswith("s3:/"):
        tmp = uri.replace("s3:/", dest_folder + "/")
    elif uri.startswith("/vsis3/"):
        tmp = uri.replace("/vsis3/", dest_folder + "/")
    else:
        _, path = os.path.splitdrive(uri)
        tmp = fsys.normpath(dest_folder + "/" + path)

    os.makedirs(fsys.justpath(tmp), exist_ok=True)
    return tmp


def equals(file1: str, file2: str, client=None) -> bool:
    """Compare the ETag of two files (S3 or local) to determine if they are equal.

    Args:
        file1 (str): First file path or S3 URI.
        file2 (str): Second file path or S3 URI.
        client: Optional boto3 S3 client instance.

    Returns:
        bool: True if the files are equal, False otherwise.
    """
    etag1 = etag(file1, client)
    etag2 = etag(file2, client)
    if etag1 and etag2:
        return etag1 == etag2
    return False


def download(uri: str, fileout: str | None = None, remove_src: bool = False, client=None) -> str | None:
    """Download a file or folder from S3 to a local destination.

    Args:
        uri (str): S3 URI of the file/folder.
        fileout (str | None): Optional local output path.
        remove_src (bool): If True, delete the source after downloading.
        client: Optional boto3 S3 client instance.

    Returns:
        str | None: Path to the downloaded file, or None on failure.
    """
    bucket_name, key = get_bucket_name_key(uri)
    if bucket_name:
        try:
            client = get_client(client)

            if key and not key.endswith("/"):
                if not fileout:
                    fileout = tempname4S3(uri)
                if os.path.isdir(fileout):
                    fileout = f"{fileout}/{fsys.justfname(key)}"
                if os.path.isfile(fileout) and equals(uri, fileout, client):
                    Logger.debug(f"using cached file {fileout}")
                else:
                    Logger.debug(f"downloading {uri} into {fileout}...")
                    os.makedirs(fsys.justpath(fileout), exist_ok=True)
                    client.download_file(Filename=fileout, Bucket=bucket_name, Key=key)
                    if remove_src:
                        client.delete_object(Bucket=bucket_name, Key=key)
            else:
                objects = client.list_objects_v2(Bucket=bucket_name, Prefix=key)["Contents"]
                for obj in objects:
                    pathname = obj["Key"]
                    if not pathname.endswith("/"):
                        dst = fileout
                        pathname = pathname.replace(key, "")
                        download(f"{uri.rstrip('/')}/{pathname}", f"{dst}/{pathname}", client)

        except ClientError as ex:
            if _USE_EXCEPTIONS:
                raise ex
            return None
        except NoCredentialsError as ex:
            if _USE_EXCEPTIONS:
                raise ex
            return None

    return fileout if os.path.isfile(fileout) else None


def upload(filename: str, uri: str, remove_src: bool = False, client=None) -> str | None:
    """Upload a local file to an S3 URI. Optionally delete the source file.

    Args:
        filename (str): Local file path to upload.
        uri (str): Target S3 URI.
        remove_src (bool): If True, delete the local file after upload.
        client: Optional boto3 S3 client instance.

    Returns:
        str | None: Path to the uploaded file, or None on failure.
    """

    # Upload the file
    try:
        bucket_name, key = get_bucket_name_key(uri)
        if bucket_name and key and filename and os.path.isfile(filename):
            client = get_client(client)
            if equals(uri, filename, client):
                Logger.debug(f"file {filename} already uploaded")
            else:
                Logger.debug(f"uploading {filename} into {bucket_name}/{key}...")
                extra_args = {}
                client.upload_file(Filename=filename, Bucket=bucket_name, Key=key, ExtraArgs=extra_args)

            if remove_src:
                Logger.debug(f"removing {filename}")
                os.unlink(filename)  # unlink and not ogr_remove!!!
            return filename

    except ClientError as ex:
        if _USE_EXCEPTIONS:
            raise ex
    except NoCredentialsError as ex:
        if _USE_EXCEPTIONS:
            raise ex

    return None


def list_files(s3_uri: str, filename_prefix: str = "", client=None, retrieve_properties: list[str] = []) -> list[str] | list[dict]:
    """List files in an S3 bucket with an optional prefix and metadata.

    Args:
        s3_uri (str): S3 URI of the bucket.
        filename_prefix (str): Prefix to filter files.
        client: Optional boto3 S3 client instance.
        retrieve_properties (list[str]): Metadata properties to include.

    Returns:
        list[str] | list[dict]: List of file keys or dictionaries with metadata.
    """
    parsed_uri = urlparse(s3_uri)
    bucket_name = parsed_uri.netloc
    prefix = os.path.join(
        s3_uri[
            s3_uri.index(urlparse(s3_uri).netloc) + len(urlparse(s3_uri).netloc) + 1 :
        ],
        filename_prefix,
    ).replace("\\", "/")

    client = get_client(client)
    paginator = client.get_paginator("list_objects_v2")

    file_list = []

    if len(retrieve_properties) > 0:
        avaliable_properties = [
            "Key",  # Full path of the object in the bucket.
            "LastModified",  # Date and time of the last modification (type datetime).
            "ETag",  # Hash MD5 of the object content (useful for integrity checks).
            "Size",  # Size of the file in bytes.
            "StorageClass",  # Storage class (e.g., STANDARD, GLACIER, etc.).
            "Owner",  # Owner of the object (if RequestPayer is set to requester).
        ]
        retrieve_properties = [
            prop for prop in retrieve_properties if prop in avaliable_properties
        ]
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    file_info = {"Key": obj["Key"]} | {
                        prop: obj.get(prop) for prop in retrieve_properties
                    }
                    file_list.append(file_info)
    else:
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if "Contents" in page:
                file_list.extend([obj["Key"] for obj in page["Contents"]])

    return file_list


def generate_presigned_url(uri: str, expiration: int = 3600, client=None) -> str | None:
    """Generate a pre-signed URL for downloading an S3 object.

    Args:
        uri (str): S3 URI of the object.
        expiration (int): Expiration time in seconds.
        client: Optional boto3 S3 client instance.

    Returns:
        str | None: A pre-signed URL or None if generation fails.
    """
    bucket_name, key = get_bucket_name_key(uri)
    client = get_client(client)
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise e
        return None


def copy(source_uri: str, destination_uri: str, client=None) -> str | None:
    """Copy an object from one S3 URI to another.

    Args:
        source_uri (str): Source S3 URI.
        destination_uri (str): Destination S3 URI.
        client: Optional boto3 S3 client instance.

    Returns:
        str | None: Destination URI if successful, None otherwise.
    """
    source_bucket_name, source_key = get_bucket_name_key(source_uri)
    destination_bucket_name, destination_key = get_bucket_name_key(destination_uri)

    client = get_client(client)

    try:
        copy_source = {"Bucket": source_bucket_name, "Key": source_key}
        client.copy_object(CopySource=copy_source, Bucket=destination_bucket_name, Key=destination_key)
        return destination_uri
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise e
        return None


def delete(uri: str, client=None) -> bool:
    """Delete an object from an S3 bucket.

    Args:
        uri (str): S3 URI of the object to delete.
        client: Optional boto3 S3 client instance.

    Returns:
        bool: True if the deletion was successful, False otherwise.
    """
    bucket_name, key = get_bucket_name_key(uri)

    client = get_client(client)

    try:
        client.delete_object(Bucket=bucket_name, Key=key)
        return True
    except Exception as e:
        if _USE_EXCEPTIONS:
            raise e
        return False


def move(source_uri: str, destination_uri: str, client=None) -> str | None:
    """Move an object from one S3 URI to another by copying and deleting.

    Args:
        source_uri (str): Source S3 URI.
        destination_uri (str): Destination S3 URI.
        client: Optional boto3 S3 client instance.

    Returns:
        str | None: Destination URI if successful, None otherwise.
    """
    if copy(source_uri, destination_uri, client):
        delete(source_uri, client)
        return destination_uri
    if _USE_EXCEPTIONS:
        raise ValueError(f"Failed to move {source_uri} to {destination_uri}")
    return None
