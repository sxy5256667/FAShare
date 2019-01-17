import hashlib

from app.blog import Blog
from app.dynamo import Database

class User:
    db = Database()
    blog = Blog()

    def __init__(self):
        return

    def login(self, username, password):
        item = self.db.get_user(username)
        if item is None:
            return 'Username not exists!'
        else:
            salt = item['salt']
            hashed_password = hashlib.sha512((password + salt).encode('utf-8')).hexdigest()
            if item['password'] != hashed_password:
                return 'The password not match our record!'
            else:
                self.userInfo = item
                return True

    def register(self, username, email, password):
        response = self.db.newUser(username, email, password)
        if response is True:
            self.userInfo = self.db.get_user(username)
            return self.db.get_user(username)
        else:
            return False

    def update_info(self, userInfo, new_email, birthday):
        response = self.db.update_user(userInfo, new_email, birthday)
        userInfo = self.db.get_user(userInfo['username'])
        return userInfo

    def history(self, username, blog_title):
        response = self.db.update_history(username, blog_title)
        return response

    def liked(self, username, blog_title):
        self.db.update_liked(username, blog_title)
        return

    def disliked(self, username, blog_title):
        self.db.update_disliked(username, blog_title)
        return

    def wish(self, username, item_name):
        response = self.db.update_wish(username, item_name)
        return response

    def addblog(self, username, title):
        response = self.db.update_myblog(username, title)
        return response

    def fetch_wish(self, username):
        item = self.db.get_user(username)
        if 'wish' in item:
            records = item['wish'].split(';')
        else:
            records = []
        records = self.db.fetch_items(records)
        return records

    def fetch_his(self, username):
        item = self.db.get_user(username)
        if 'history' in item:
            records = item['history'].split(';')
            for i in range(len(records)):
                blog = self.blog.fetch_blog(records[i])
                if blog is not False:
                    blog['photos'] = blog['photos'].split(';')[0]
                    records[i] = blog
        else:
            records = []
        return records

    def fetch_blog(self, username):
        item = self.db.get_user(username)
        if 'myblog' in item:
            records = item['myblog'].split(';')
        else:
            records = []

        for i in range(len(records)):
            blog = self.blog.fetch_blog(records[i])
            blog['photos'] = blog['photos'].split(';')[0]
            records[i] = blog
        return records

    def fetch_like(self, username):
        item = self.db.get_user(username)
        if 'liked' in item:
            records = item['liked'].split(';')
            for i in range(len(records)):
                blog = self.blog.fetch_blog(records[i])
                if blog is not False:
                    blog['photos'] = blog['photos'].split(';')[0]
                    records[i] = blog
        else:
            records = []
        return records
