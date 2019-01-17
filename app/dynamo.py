import hashlib
import json
import random
import string
import uuid
from datetime import timedelta
from io import StringIO
from operator import itemgetter
from time import gmtime, strftime

import boto3
from boto3.dynamodb.conditions import Key

from app import config
from app.s3 import storage

class Database:
    dynamodb = boto3.resource('dynamodb',
                            region_name=config.region_name,
                            aws_access_key_id=config.aws_access_key_id,
                            aws_secret_access_key=config.aws_secret_access_key)

    storage = storage()

    def newUser(self, username, email, password):
        table = self.dynamodb.Table('userInfo')
        Info = self.get_user(username)

        # Check whether the user exists with user data.
        if Info is not None:
            return False
        # If the user does not exist:
        else:
            # Generate salt seed.
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()

            response = table.put_item(
                Item={
                    'username': username,
                    'password': hashed_password,
                    'salt': salt,
                    'email': email
                }
            )
            return True

    def get_user(self, username):
        table = self.dynamodb.Table('userInfo')
        response = table.get_item(
            Key={
                'username': username
            }
        )
        if 'Item' in response:
            return response['Item']
        return None

    def update_user(self, userInfo, email, birthday):
        table = self.dynamodb.Table('userInfo')
        if email is not '':
            response = table.update_item(
                Key={
                    'username': userInfo['username']
                },
                UpdateExpression="set email = :s",
                ExpressionAttributeValues={
                    ':s': email
                },
                ReturnValues="UPDATED_NEW"
            )
        if 'birthday' not in userInfo:
            if birthday is not '':
                response = table.update_item(
                    Key={
                        'username': userInfo['username']
                        },
                    UpdateExpression="set birthday = :h",
                    ExpressionAttributeValues={
                        ':h': str(birthday)
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response
        else:
            if birthday is not '':
                response = table.update_item(
                    Key={
                        'username': userInfo['username']
                    },
                    UpdateExpression="set birthday = :h",
                    ExpressionAttributeValues={
                        ':h':  birthday
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response

    def newblog(self, blog):
        table = self.dynamodb.Table('blog')
        table_time = self.dynamodb.Table('blog_date')
        Info = self.get_blog(blog['title'])

        # Check whether the user exists with user data.
        if Info is not None:
            return False
        # If the user does not exist:
        else:
            showtime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            response = table.put_item(
                Item={
                    'blog_title': blog['title'],
                    'abstract': blog['abstract'],
                    'photos': blog['photos'],
                    'tags': blog['tags'],
                    'content': blog['content'],
                    'products': blog['products'],
                    'author': blog['author']
                }
            )
            response = table_time.put_item(
                Item={
                    'blog_title': blog['title'],
                    'update_time': showtime
                }
            )
            self.sync_cloudsearch(blog)
        return True

    def get_blog(self, blogtitle):
        table = self.dynamodb.Table('blog')
        response = table.get_item(
            Key={
                'blog_title': blogtitle
            }
        )
        if 'Item' in response:
            return response['Item']
        return None

    def addAds(self, ads):
        table = self.dynamodb.Table('ads')
        response= {'Item': True}
        ads_id = ''
        while 'Item' in response:
            ads_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            response = table.get_item(
                Key={
                    'ads_id': ads_id
                }
            )
        response = table.put_item(
            Item={
                'ads_id': ads_id,
                'ads_pic': ads['pic'],
                'ads_url': ads['url']
            }
        )
        return response

    def list_ads(self):
        table = self.dynamodb.Table('ads')
        response = table.scan()
        records = []

        for i in response['Items']:
            records.append(i)
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for i in response['Items']:
                records.append(i)
        return records

    def list_blog(self):
        table = self.dynamodb.Table('blog')
        response = table.scan()
        records = []

        for i in response['Items']:
            records.append(i)
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for i in response['Items']:
                records.append(i)
        return records

    def list_new(self):
        table_time = self.dynamodb.Table('blog_date')
        response = table_time.scan()
        records = []

        for i in response['Items']:
            records.append(i)
        while 'LastEvaluatedKey' in response:
            response = table_time.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for i in response['Items']:
                records.append(i)

        newlist = sorted(records, key=itemgetter('update_time'), reverse=True)
        records = []

        for i in newlist:
            records.append(self.get_blog(i['blog_title']))

        return records[0:4]

    def update_history(self, username, history):
        table = self.dynamodb.Table('userInfo')
        userInfo = self.get_user(username)
        if 'history' not in userInfo:
            table.update_item(
                Key={
                    'username': username
                    },
                UpdateExpression="set history = :h",
                ExpressionAttributeValues={
                    ':h': str(history)
                },
                ReturnValues="UPDATED_NEW"
            )
            return
        else:
            if history not in userInfo['history'].split(';'):
                table.update_item(
                    Key={
                        'username': username
                    },
                    UpdateExpression="set history = :h",
                    ExpressionAttributeValues={
                        ':h':  userInfo['history'] +';' +history
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return

    def update_liked(self, username, liked):
        table = self.dynamodb.Table('userInfo')
        userInfo = self.get_user(username)
        if 'liked' not in userInfo:
            response = table.update_item(
                Key={
                    'username': username
                    },
                UpdateExpression="set liked = :h",
                ExpressionAttributeValues={
                    ':h': str(liked)
                },
                ReturnValues="UPDATED_NEW"
            )
            return response
        else:
            if liked not in userInfo['liked'].split(';'):
                response = table.update_item(
                    Key={
                        'username': username
                    },
                    UpdateExpression="set liked = :h",
                    ExpressionAttributeValues={
                        ':h':  userInfo['liked'] +';' + liked
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response

    def update_disliked(self, username, disliked):
        table = self.dynamodb.Table('userInfo')
        userInfo = self.get_user(username)
        if 'disliked' not in userInfo:
            response = table.update_item(
                Key={
                    'username': username
                },
                UpdateExpression="set disliked = :h",
                ExpressionAttributeValues={
                    ':h': str(disliked)
                },
                ReturnValues="UPDATED_NEW"
            )
            return response
        else:
            if disliked not in userInfo['disliked'].split(';'):
                response = table.update_item(
                    Key={
                        'username': username
                    },
                    UpdateExpression="set disliked = :h",
                    ExpressionAttributeValues={
                        ':h': userInfo['disliked'] + ';' + disliked
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response

    def create_item(self, item_name, image, brand, price, link):
        table = self.dynamodb.Table('item')
        path = self.storage.upload_itemimage(image, image.filename)

        response = table.get_item(
            Key={
                'item_name': item_name,
            }
        )
        if 'Item' in response:
            return False

        response = table.put_item(
            Item={
                'item_name': item_name,
                'image': path,
                'brand': brand,
                'price': price,
                'link': link
            }
        )
        return

    def list_items(self):
        table = self.dynamodb.Table('item')
        response = table.scan()
        records = []

        for i in response['Items']:
            records.append(i)
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for i in response['Items']:
                records.append(i)
        return records

    def fetch_items(self, items):
        table = self.dynamodb.Table('item')
        records = []
        for i in items:
            response = table.get_item(
                Key={
                    'item_name': i
                }
            )
            if 'Item' in response:
                records.append(response['Item'])
        return records

    def update_wish(self, username, wish):
        table = self.dynamodb.Table('userInfo')
        userInfo = self.get_user(username)
        if 'wish' not in userInfo:
            response = table.update_item(
                Key={
                    'username': username
                    },
                UpdateExpression="set wish = :h",
                ExpressionAttributeValues={
                    ':h': str(wish)
                },
                ReturnValues="UPDATED_NEW"
            )
            return response
        else:
            if wish not in userInfo['wish'].split(';'):
                response = table.update_item(
                    Key={
                        'username': username
                    },
                    UpdateExpression="set wish = :h",
                    ExpressionAttributeValues={
                        ':h':  userInfo['wish'] +';' +wish
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response

    def update_myblog(self, username, title):
        table = self.dynamodb.Table('userInfo')
        userInfo = self.get_user(username)
        if 'myblog' not in userInfo:
            response = table.update_item(
                Key={
                    'username': username
                    },
                UpdateExpression="set myblog = :h",
                ExpressionAttributeValues={
                    ':h': str(title)
                },
                ReturnValues="UPDATED_NEW"
            )
            return response
        else:
            if title not in userInfo['myblog'].split(';'):
                response = table.update_item(
                    Key={
                        'username': username
                    },
                    UpdateExpression="set myblog = :h",
                    ExpressionAttributeValues={
                        ':h':  userInfo['myblog'] +';' +title
                    },
                    ReturnValues="UPDATED_NEW"
                )
                return response

    def sync_cloudsearch(self, blog):
        showtime = strftime("%Y%m%d%H%M%S", gmtime())

        letters = string.ascii_lowercase
        rand = ''.join(random.choice(letters) for i in range(2))

        array = [
            {"type": "add",
             "id": showtime + rand,
             "fields": {
                'blog_title': blog['title'],
                'abstract': blog['abstract'],
                'photos': blog['photos'],
                'tags': blog['tags'],
                'content': blog['content'],
                'products': blog['products'],
                'author': blog['author']
                }
             }
        ]

        client = boto3.client('cloudsearchdomain',
                              endpoint_url='XXX',
                              region_name=config.region_name,
                              aws_access_key_id=config.aws_access_key_id,
                              aws_secret_access_key=config.aws_secret_access_key
                              )

        io = StringIO()
        json.dump(array, io)

        response = client.upload_documents(
            documents=io.getvalue(),
            contentType='application/json'
        )
