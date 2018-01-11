from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    created = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.created = datetime.utcnow()
        self.owner = owner

    def is_valid(self):
        if self.title and self.body and self.created:
            return True
        else:
            return False

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'blog', 'index', ]
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password,user.pw_hash):
            session['username'] = username
            flash("Logged in")
            return redirect('/main')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']


        if len(username) is 0 or len(password) is 0:
            flash("Must provide username and password!")
            return render_template('register.html', username=username, password=password)

        if password != verify:
            flash('Passwords do not match!')
            return render_template('register.html', username=username)

        if len(username)<3 or len(password)<3:
            flash('Username and password must be atleast 3 characters in length!')
            return render_template('register.html', username=username)

        # TODO - validate user's data

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/main')
        else:
            flash('User already exists')
            return render_template('register')

    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/main')


@app.route("/main", methods=['GET'])
def index():
    all_users = User.query.all()
    return render_template ('index.html', all_users=all_users)


@app.route("/blog", methods=['POST', 'GET'])
def display_blog():
    blog_id = request.args.get('id')
    user_id = request.args.get('user')

    if blog_id:
        blog_entry = Blog.query.get(blog_id)
        return render_template('single_entry.html', blog_entry=blog_entry)
    if user_id:
        user_entry = User.query.get(user_id)
        return render_template("single_user.html", user=user_entry)

    new_post = Blog.query.all()
    return render_template ("blog.html", new_post=new_post)




@app.route("/new_entry", methods=['POST','GET'])
def new_entry():
    if request.method == 'POST':
        new_entry_title = request.form['title']
        new_entry_body = request.form['body']
        owner = User.query.filter_by(username=session['username']).first()
        new_entry = Blog(new_entry_title, new_entry_body, owner)

        if new_entry.is_valid():
            db.session.add(new_entry)
            db.session.commit()
            url = "/blog?id=" + str(new_entry.id)
            return redirect(url)

        else:
            flash("Both a Title and Body are required")
            return render_template('new_entry_form.html', title = "Create your blog post!",
                new_entry_title=new_entry_title, new_entry_body=new_entry_body)

    else:
        return render_template('new_entry_form.html', title = "Create your blog post!")




if __name__ == '__main__':
    app.run()