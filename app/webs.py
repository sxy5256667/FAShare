import os
from xml.dom import minidom

import boto3
from flask import render_template, request, session, redirect, url_for
import re
from functools import wraps

from jinja2 import Environment, FileSystemLoader

from app import webapp, config
from app.blog import Blog
from app.dynamo import Database
from app.user import User

webapp.secret_key = os.urandom(24)
Pattern = re.compile("^[^\s@]+@[^\s@]+\.[^\s@]+$")

db = Database()
blog = Blog()
user = User()

dic = {}
# Login required decorator for login status checking
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('auth' in session) and (session['username'] is not None):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@webapp.route('/', methods=['GET', 'POST'])
def main():
    login_status = False
    ads = db.list_ads()
    # return render_template('main.html', login=Login_status, ads=ads)
    blogs = blog.fetch_new()
    if len(blogs) >= 4:
        blogs = blogs[0:4]
    if 'auth' in session and (session['username'] is not None):
        login_status = True
        wish = user.fetch_wish(session['username'])
        reco = recommend(wish)
        if len(reco) >4:
            reco = reco[0:4]
        return render_template('main.html', login=login_status, title='FAshare', username=session['username'], ads=ads,
                               blogs = blogs, recommend = reco)
    else:
        login_status = False
        return render_template('main.html', login=login_status, title='FAshare', ads=ads,
                               blogs = blogs)

@webapp.route('/search', methods=['GET', 'POST'])
def search():
    login_status = False
    text = request.form.get('search')
    response = search_blog(text)
    username = ""
    if 'auth' in session and (session['username'] is not None):
        login_status = True
        username = session['username']

    return render_template('search.html', login=login_status, title='FAshare', username=username, query = text, blogs = response)


@webapp.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function defines the welcome page of the website,
    where authentication is required.
    """
    if request.method == 'POST':
        # Receive the context of submitted form.
        username = request.form.get('username')
        password = request.form.get('password')

        # If an incomplete form been detected:
        if username == '' or password == '':
            # No username input.
            if request.form.get('username') == "":
                errorLogin = True
                errorMessage = "Please enter username."
            # No password input.
            else:
                errorLogin = True
                errorMessage = "Please enter password."

        else:
            response = user.login(username, password)
            if response is True:
                session['auth'] = True
                session['username'] = username
                return main()
            else:
                errorLogin = True
                errorMessage = response

            return render_template('sign_in.html', errorLogin=errorLogin, errorMessage=errorMessage, username=username,
                                   password=password, title="login")
    return render_template('sign_in.html', title="login")


@webapp.route('/register', methods=['GET', 'POST'])
def register():
    """
    This function defines the functionality of new user registration.
    """
    if request.method == 'POST':
        errorCreateUser = False
        errorMessage = ""
        # Receive the data from registration form
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        # Check for incomplete data.
        if (username == "") or (email == '') or (password == "") or (password2 == ""):
            if username == "":
                errorCreateUser = True
                errorMessage = "Please enter username."
            elif email == "":
                errorCreateUser = True
                errorMessage = "Please enter email address."
            elif password == "":
                errorCreateUser = True
                errorMessage = "Please enter password."
            else:
                errorCreateUser = True
                errorMessage = "Please re-enter password."
            return render_template('register.html', errorCreateUser=errorCreateUser, errorMessage=errorMessage,
                                   username=username, password=password, password2=password2)
        elif (re.search(r'(\w+)', username).group() != username) or (re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email).group() != email) \
                or ((re.search(r'[a-z]', password)) is None) or ((re.search(r'[A-Z]', password)) is None) \
                or ((re.search(r'[0-9]', password)) is None) or (password != password2):
            errorCreateUser = True
            errorMessage = "Invalid Information."
            return render_template('register.html', errorCreateUser=errorCreateUser, errorMessage=errorMessage,
                               username=username, password=password, password2=password2)
        else:
            response = user.register(username, email, password)
            if response is not False:
                session['auth'] = True
                session['username'] = username
                return main()
            else:
                errorCreateUser = True
                errorMessage = "Username already exists!"
                return render_template('register.html', errorCreateUser=errorCreateUser, errorMessage=errorMessage,
                                       username=username, password=password, password2=password2)

    return render_template('register.html')


@webapp.route('/logout')
def logout():
    if 'auth' in session:
        session.pop('auth', None)
    if 'username' in session:
        session.pop('username', None)
    return main()


def Tags():
    cwd = os.path.dirname(os.path.realpath(__file__))
    xmldoc = minidom.parse(cwd+'/tags.xml')
    itemlist = xmldoc.getElementsByTagName('item')
    tag = []
    for s in itemlist:
        tag.append(s.attributes['name'].value)

    return tag


@webapp.route('/<string:username>/upload_blog', methods=['GET', 'POST'])
@login_required
def upload_blog(username):
    error = False
    items = db.list_items()
    tag = Tags()
    global dic
    if username not in dic:
        dic[username] = {}
    if request.method == 'POST' and request.form['upload_form'] == 'upload_photo':
        if 'upload_photo' in request.files:
            file = request.files['upload_photo']
            dic[username][file.filename] = file.stream.read()
            title = request.form.get('blog_title')
            ads = request.form.get('blog_abs')
            content = request.form.get('blog_cont')
            return render_template('upload_blog.html', login=session['auth'],username=session['username'], title="Upload Blog",
                                   images=dic[username], error=error,blog_title=title, ads=ads, content=content,
                                   items = items, tag = tag)
    elif request.method == 'POST' and request.form['upload_form'] == 'upload_all':
        images_path = blog.upload_images(dic[username])
        title = request.form.get('blog_title')
        ads = request.form.get('blog_abs')
        tags = ';'.join(request.form.getlist('blog_tags'))
        content = request.form.get('blog_cont')
        products = ';'.join(request.form.getlist('blog_products'))

        blank = (images_path == "") or (title == '') or (ads == "") or (tags == "") or (content == "") or (products == '')

        if blank is True:
            error = True
            errorMessage = 'One or more field is blank!'
            return render_template('upload_blog.html', title="Upload Blog", login=session['auth'], username=session['username'],
                                   images=dic[username],  error=error, errorMessage=errorMessage,
                                   blog_title=title, ads=ads, content=content, items = items, tag = tag)
        else:
            blog_info = {
                'title': title,
                'abstract': ads,
                'photos': images_path,
                'tags': tags,
                'content': content,
                'products': products,
                'author': session['username']
            }
            response = blog.new_blog(blog_info)
            if response == True:
                user.addblog(session['username'], title)
                dic.pop(username, None)
                return redirect(url_for('main'))
            else:
                error = True
                return render_template('upload_blog.html', title="Upload Blog", login=session['auth'],  username=session['username'],
                                       images=dic[username], error=error, errorMessage=response, items = items, tag = tag)
    return render_template('upload_blog.html', title="Upload Blog", login=session['auth'],  username=session['username'],
                           images=dic[username], error=error, items = items, tag = tag)


@webapp.route('/upload_item', methods=['GET', 'POST'])
@login_required
def upload_item():
    if request.method == 'POST':
        title = request.form.get('item_title')
        brand = request.form.get('item_brand')
        price = request.form.get('item_price')
        link = request.form.get('item_link')
        if 'upload_photo' in request.files:
            file = request.files['upload_photo']
        else:
            error = True
            errorMessage = 'Please upload a image!'
            return render_template('upload_item.html', login=session['auth'], username=session['username'], title="Upload Blog",
                                   error=error, errorMessage = errorMessage, item_name=title,
                                   brand = brand, price = price,link = link)

        blank = (title == "") or (brand == '') or (price == "") or (link == "")

        if blank is True:
            error = True
            errorMessage = 'One or more field is blank!'
            return render_template('upload_item.html', title="Upload Blog", login=session['auth'],
                                   username=session['username'],  error=error, errorMessage=errorMessage,
                                   item_name=title, brand=brand, pricet=price, links=link)
        else:
            response = db.create_item(title, file, brand, price, link)
            if response == False:
                return render_template('upload_item.html', title="Upload Item", login=session['auth'],
                                       username=session['username'], error = True, errorMessage = 'Item already exists!')
            else:
                return redirect(url_for('upload_blog', username = session['username']))

    return render_template('upload_item.html', title="Upload Item", login=session['auth'],  username=session['username'])

@webapp.route('/blog/<string:blog_title>/', methods=['GET', 'POST'])
@login_required
def blog_web(blog_title):
    button_like = 0
    add_history(session['username'], blog_title)
    userInfo = db.get_user(session['username'])
    # Check whether the blog is liked or disliked
    if 'liked' in userInfo:
        like_record = userInfo['liked']
        if blog_title in like_record.split(';'):
            button_like = 1
    if 'disliked' in userInfo:
        dislike_record = userInfo['disliked']
        if blog_title in dislike_record.split(';'):
            button_like = 2
    Info = blog.fetch_blog(blog_title)
    images = Info['photos'].split(';')[:-1]
    tags = Info['tags'].split(';')
    items = Info['products'].split(';')
    items = db.fetch_items(items)
    author = Info['author']

    content = Info['content'].split('\r\n')
    return render_template("blog.html", title= Info['blog_title'], login=session['auth'], username=userInfo['username'],
                           button_like=button_like, abstract=Info['abstract'], content = content, images = images, tags = tags,
                           items = items, author = author)

@webapp.route('/<string:username>/editinfo', methods=['GET', 'POST'])
@login_required
def editinfo(username):
    birthday = ''
    userInfo = db.get_user(username)
    # Update Email
    old_email = userInfo['email']
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    Update_state = False
    UpdateMessage = ''
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        birthday = request.form.get('birthday')
        if Pattern.match(new_email).group() != new_email:
            Update_state = True
            UpdateMessage = 'Email format is wrong!'
        else:
            Update_state = True
            UpdateMessage = 'Upload Success!'
            response = user.update_info(userInfo, new_email, birthday)
            return render_template('edit_profile.html', login=session['auth'], username=username,
                                email=new_email, birthday=response['birthday'], Update_state=Update_state,
                                   UpdateMessage=UpdateMessage)

    return render_template('edit_profile.html',login=session['auth'], username=username,email=old_email, birthday=birthday,
                           Update_state=Update_state, UpdateMessage=UpdateMessage)

@webapp.route('/personalmainpage/<string:username>')
@login_required
def personalmainpage(username):
    # Check if having history
    userInfo = db.get_user(username)
    his_blogs = user.fetch_his(username)
    if len(his_blogs) == 0:
        history = True
    else:
        history = False
        if len(his_blogs) >= 4:
            his_blogs = his_blogs[-4:]
        his_blogs = his_blogs[::-1]

    # Check if liking blogs
    liked_blogs = user.fetch_like(username)[::-1]
    if len(liked_blogs) == 0:
        liked = True
    else:
        liked = False
        if len(liked_blogs) >= 4:
            liked_blogs = liked_blogs[-4:]
        else:
            liked_blogs = liked_blogs[::-1]

    birthday = ""
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    return render_template('personalmainpage.html', login=session['auth'], title='FAshare', username=userInfo['username'],
                           email=userInfo['email'],birthday = birthday, history=history, liked=liked, his_blogs=his_blogs, liked_blogs=liked_blogs)


@webapp.route('/personal-history-<string:username>/<int:id>')
@login_required
def personalhis(username, id = 0):
    userInfo = db.get_user(username)
    his_blogs = user.fetch_his(username)
    if len(his_blogs) == 0:
        history = True
    else:
        history = False
        if len(his_blogs) >= (id +20):
            his_blogs = his_blogs[id-1:(id+20):-1]
        else:
            his_blogs = his_blogs[(id-1)::-1]

    birthday = ""
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    return render_template('personalhis.html', login=session['auth'], title='FAshare', username=userInfo['username'],
                           email=userInfo['email'], birthday = birthday, history=history, his_blogs=his_blogs, id=id)


@webapp.route('/personal-like-<string:username>/<int:id>')
@login_required
def personallike(username, id = 0):
    userInfo = db.get_user(username)
    liked_blogs = user.fetch_like(username)[::-1]
    if len(liked_blogs) == 0:
        liked = True
    else:
        liked = False
        if len(liked_blogs) >= (id +20):
            liked_blogs = liked_blogs[id-1:(id+20):-1]
        else:
            liked_blogs = liked_blogs[(id-1)::-1]

    birthday = ""
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    return render_template('personallike.html', login=session['auth'], title='FAshare', username=userInfo['username'],
                           email=userInfo['email'], birthday = birthday, liked=liked, liked_blogs=liked_blogs, id=id)


@webapp.route('/personal-blog-<string:username>/<int:id>')
@login_required
def personalblog(username, id = 0):
    # return render_template('personalmainpage.html', login=Login_status, ads=ads)
    userInfo = db.get_user(username)
    myblogs = user.fetch_blog(username)
    if len(myblogs) >= (id +20):
        myblogs = myblogs[id-1:(id+20):-1]
    else:
        myblogs = myblogs[(id-1)::-1]

    birthday = ""
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    return render_template('personalblog.html', login=session['auth'], title='FAshare', username=userInfo['username'], birthday = birthday,
                           myblogs=myblogs, id=id, email=userInfo['email'])


@webapp.route('/personal-wish-<string:username>/<int:id>')
@login_required
def personal_wish(username, id = 0):
    # return render_template('personalmainpage.html', login=Login_status, ads=ads)
    userInfo = db.get_user(username)
    wish = user.fetch_wish(username)
    if len(wish) >= (id +20):
        wish = wish[id-1:(id+20):-1]
    else:
        wish = wish[(id-1)::-1]

    birthday = ""
    if 'birthday' in userInfo:
        birthday = userInfo['birthday']

    return render_template('personal_wish.html', login=session['auth'], title='FAshare', username=userInfo['username'],
                           wish=wish,birthday = birthday, id=id, email=userInfo['email'])

def search_blog(text):
    client = boto3.client('cloudsearchdomain',
                          endpoint_url='XXX',
                          region_name=config.region_name,
                          aws_access_key_id=config.aws_access_key_id,
                          aws_secret_access_key=config.aws_secret_access_key
                          )

    text = text.split(' ')
    search = ""

    for i in text:
        search  =  search + "'" + i + "'"

    query = "(or " + search + ")"

    response = client.search(
        query= query,
        queryParser='structured',
        returnFields='blog_title,photos,abstract',
        size=10
    )
    response = response['hits']['hit']

    records = []

    for i in range(len(response)):
        records.append(response[i]['fields'])
        image = records[i]['photos'][0].split(';')[0]
        records[i]['photos'] = image

    return records


def recommend(wish):
    client = boto3.client('cloudsearchdomain',
                          endpoint_url='XXX',
                          region_name=config.region_name,
                          aws_access_key_id=config.aws_access_key_id,
                          aws_secret_access_key=config.aws_secret_access_key
                          )
    search = ""

    if len(wish) == 0:
        return ""

    for i in wish:
        search = search + "'" + i['item_name'] + "'"

    query = "(or " + search + ")"

    response = client.search(
        query= query,
        queryParser='structured',
        returnFields='blog_title,photos,abstract',
        size=10
    )
    response = response['hits']['hit']

    records = []

    for i in range(len(response)):
        records.append(response[i]['fields'])
        image = records[i]['photos'][0].split(';')[0]
        records[i]['photos'] = image

    return records


@webapp.route('/likes_dislikes-<string:blog_title>', methods=['GET', 'POST'])
@login_required
def like_dislike(blog_title):
    username = session['username']
    if request.method == 'POST':
        value = request.form.get('up_down')
        if value == 'like':
            add_liked(username, blog_title)
            return redirect(url_for('blog_web', blog_title=blog_title))
        elif value == 'dislike':
            add_dislike(username, blog_title)
            return redirect(url_for('blog_web', blog_title=blog_title))


@webapp.route('/wish/<string:item_name>/<string:title>')
@login_required
def wish(item_name, title):
    add_wish(session['username'], item_name)
    return redirect(url_for('blog_web', login=session['auth'], title='FAshare', username=session['username'],blog_title = title))

def add_liked(username, blog_title):
    response = user.liked(username, blog_title)
    return response

def add_dislike(username, blog_title):
    user.disliked(username, blog_title)
    return

def add_wish(username, item_name):
    response = user.wish(username, item_name)
    return response

def add_history(username, blog_title):
    response = user.history(username, blog_title)
    return response




