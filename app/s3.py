import os
import random
import string

from app import webapp, config

import boto3

class storage:

    def __init__(self):
        self.bucket = config.bucket_name
        return

    def view_bucket(self):
        s3 = boto3.resource('s3',
                            region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id,
                            aws_secret_access_key=config.aws_secret_access_key
                            )

        bucket = s3.Bucket(self.bucket)
        keys = bucket.objects.all()
        return keys

    def fetch_ads(self, filename):
        client = boto3.client('s3',
                            region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id,
                            aws_secret_access_key=config.aws_secret_access_key
                            )

        key = 'ads' + '/' + filename
        url = '{}/{}/{}'.format(client.meta.endpoint_url, self.bucket, key)

        return url

    def upload_blogimage(self, image, filename):
        key = 'blogs' + '/'
        name, ext = os.path.split(filename)
        s3 = boto3.client('s3',
                          region_name=config.region_name,
                          aws_access_key_id=config.aws_access_key_id,
                          aws_secret_access_key=config.aws_secret_access_key)

        results = {'Contents': True}
        name = ''

        while 'Contents' in results:
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            filename = name + ext
            results = s3.list_objects(Bucket=self.bucket, Prefix=key+filename)

        s3.put_object(Bucket=self.bucket,
                          Key=key+filename,
                          Body=image,
                          ACL='public-read')

        path = self.fetch_blogimage(filename)
        return path

    def fetch_blogimage(self, filename):
        client = boto3.client('s3',
                              region_name=config.region_name,
                              aws_access_key_id=config.aws_access_key_id,
                              aws_secret_access_key=config.aws_secret_access_key
                              )

        key = 'blogs' + '/' + filename
        url = '{}/{}/{}'.format(client.meta.endpoint_url, self.bucket, key)
        return url

    def upload_itemimage(self, file, filename):
        key = 'items' + '/'
        name, ext = os.path.split(filename)
        s3 = boto3.client('s3',
                          region_name=config.region_name,
                          aws_access_key_id=config.aws_access_key_id,
                          aws_secret_access_key=config.aws_secret_access_key)

        results = {'Contents': True}
        name = ''

        while 'Contents' in results:
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            filename = name + ext
            results = s3.list_objects(Bucket=self.bucket, Prefix=key + filename)

        s3.put_object(Bucket=self.bucket,
                      Key=key + filename,
                      Body=file,
                      ACL='public-read')

        path = self.fetch_itemimage(filename)
        return path

    def fetch_itemimage(self, filename):
        client = boto3.client('s3',
                              region_name=config.region_name,
                              aws_access_key_id=config.aws_access_key_id,
                              aws_secret_access_key=config.aws_secret_access_key
                              )

        key = 'items' + '/' + filename
        url = '{}/{}/{}'.format(client.meta.endpoint_url, self.bucket, key)
        return url



