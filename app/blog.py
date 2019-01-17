from app.dynamo import Database
from app.s3 import storage

class Blog:
    db = Database()
    storage = storage()

    def new_blog(self, blog):
        response = self.db.newblog(blog)

        if response is True:
            return True
        else:
            return 'Blog Title already exists!'

    def upload_images(self, images):
        image_path = ''
        for key, value in images.items():
            path = self.storage.upload_blogimage(value, key)
            image_path += path + ';'

        return image_path

    def upload_blog(self, blog):
        response = self.db.newblog(blog)
        if response is False:
            return 'Blog title already exists!'
        else:
            return True

    def fetch_blog(self, title):
        response = self.db.get_blog(title)
        if response is None:
            return False
        return response

    def fetch_list(self):
        records = self.db.list_blog()

        for i in range(len(records)):
            image = records[i]['photos'].split(';')[0]
            records[i]['photos'] = image

        return records

    def fetch_new(self):
        records = self.db.list_new()

        for i in range(len(records)):
            print(records[i])
            image = records[i]['photos'].split(';')[0]
            records[i]['photos'] = image

        return records

