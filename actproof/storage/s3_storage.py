"""
AWS S3 storage backend
Also compatible with S3-compatible services (Cloudflare R2, MinIO, etc.)
"""

import json
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
from .base import StorageBackend


class S3Storage(StorageBackend):
    """AWS S3 storage implementation"""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "eu-central-1",
        endpoint_url: Optional[str] = None,  # For S3-compatible services
    ):
        """
        Initialize S3 storage

        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region
            endpoint_url: Custom endpoint URL (for Cloudflare R2, MinIO, etc.)
        """
        self.bucket_name = bucket_name

        # Configure boto3 client
        config = Config(
            signature_version='s3v4',
            region_name=region_name
        )

        client_kwargs = {
            'config': config,
            'region_name': region_name,
        }

        if aws_access_key_id and aws_secret_access_key:
            client_kwargs['aws_access_key_id'] = aws_access_key_id
            client_kwargs['aws_secret_access_key'] = aws_secret_access_key

        if endpoint_url:
            client_kwargs['endpoint_url'] = endpoint_url

        self.s3_client = boto3.client('s3', **client_kwargs)

        # Verify bucket exists or create it
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists, create if it doesn't"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ S3 bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404' or error_code == '403':
                # Bucket doesn't exist or access denied, try to create it
                logger.info(f"Bucket '{self.bucket_name}' not found or access denied. Attempting to create...")
                try:
                    # us-east-1 doesn't require LocationConstraint
                    region = self.s3_client.meta.region_name
                    if region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': region
                            }
                        )
                    logger.info(f"✅ Created S3 bucket '{self.bucket_name}' in region '{region}'")
                except ClientError as create_error:
                    error_code = create_error.response.get('Error', {}).get('Code', 'Unknown')
                    error_msg = create_error.response.get('Error', {}).get('Message', str(create_error))
                    if error_code == 'BucketAlreadyExists':
                        logger.info(f"Bucket '{self.bucket_name}' already exists (owned by another account)")
                    elif error_code == 'BucketAlreadyOwnedByYou':
                        logger.info(f"Bucket '{self.bucket_name}' already owned by you")
                    else:
                        logger.warning(f"Could not create bucket '{self.bucket_name}': {error_code} - {error_msg}")
                        # Don't raise - bucket might exist but we don't have permission to check
                except Exception as create_error:
                    logger.warning(f"Unexpected error creating bucket: {create_error}")
                    # Don't raise - bucket might exist
            else:
                # Other error (e.g., 403 Forbidden) - bucket might exist but we don't have permission
                logger.warning(f"Could not verify bucket '{self.bucket_name}': {error_code} - {e.response.get('Error', {}).get('Message', 'Unknown error')}")
                # Don't raise - continue anyway, might work for operations

    def save_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Save file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
                ServerSideEncryption='AES256'  # Encryption at rest
            )
            return f"s3://{self.bucket_name}/{key}"
        except ClientError as e:
            raise RuntimeError(f"Failed to save file to S3: {e}")

    def save_json(self, key: str, data: dict) -> str:
        """Save JSON data to S3"""
        json_data = json.dumps(data, indent=2).encode("utf-8")
        return self.save_file(key, json_data, content_type="application/json")

    def get_file(self, key: str) -> bytes:
        """Retrieve file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {key}")
            raise RuntimeError(f"Failed to retrieve file from S3: {e}")

    def get_json(self, key: str) -> dict:
        """Retrieve JSON data from S3"""
        data = self.get_file(key)
        return json.loads(data.decode("utf-8"))

    def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            raise RuntimeError(f"Failed to delete file from S3: {e}")

    def file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise RuntimeError(f"Failed to check file existence: {e}")

    def get_download_url(self, key: str, expiration: int = 3600) -> str:
        """
        Generate pre-signed download URL

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Pre-signed URL for downloading the file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate pre-signed URL: {e}")

    def list_files(self, prefix: str = "") -> list[str]:
        """List files with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]
        except ClientError as e:
            raise RuntimeError(f"Failed to list files: {e}")

    def get_upload_url(self, key: str, expiration: int = 3600, content_type: str = "application/octet-stream") -> str:
        """
        Generate pre-signed upload URL for direct client-side uploads

        Args:
            key: S3 object key
            expiration: URL expiration time in seconds
            content_type: Expected content type

        Returns:
            Pre-signed URL for uploading a file
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate pre-signed upload URL: {e}")
