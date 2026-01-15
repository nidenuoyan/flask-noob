# 第一步：导入所有必要模块（按功能分类，清晰有序）
from flask import Flask, url_for, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
import click

# 第二步：初始化Flask应用
app = Flask(__name__)

# 第三步：配置应用参数（集中管理，便于修改）
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost:3306/flask_movie_db?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 第四步：初始化扩展（db、login_manager，紧跟配置）
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # 配置登录页面路由，未登录用户重定向至此

# 第五步：定义数据模型（User、Movie，扩展初始化后）
class User(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

# 第六步：用户加载回调函数（login_manager必需，紧跟模型定义）
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

# 第七步：定义cli命令（admin，创建/更新管理员）
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create or update admin user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')

# 第八步：上下文处理器（传递user变量给所有模板）
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)

# 第九步：初始化数据库表和默认数据（应用上下文内执行）
with app.app_context():
    db.create_all()
    if not User.query.first():
        user = User(name='Zhang Qi', username='zhangqi')
        user.set_password('123456')  # 补充：给默认用户设置密码，便于登录
        db.session.add(user)
        db.session.commit()

# 第十步：定义视图函数（按访问优先级排序，核心功能在前）
## 1. 主页视图（核心）
@app.route('/',methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 认证判断（current_user已导入，可正常使用）
        if not current_user.is_authenticated:
            flash('Please login first to add movies.')
            return redirect(url_for('index'))
        
        # 原有表单处理逻辑
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('index'))
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    # 补充返回语句，渲染模板
    user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', user=user, movies=movies)

## 2. 登录视图
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        # 修复：按用户名查询用户，而非取第一个用户
        user = User.query.filter_by(username=username).first()
        if user and user.validate_password(password):  # 先判断用户是否存在，再验证密码
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')

## 3. 登出视图
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))

## 4. 设置视图
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')

## 5. 编辑视图
@app.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Movie updated.')
        return redirect(url_for('index'))
    
    return render_template('edit.html', movie=movie)

## 6. 删除视图（仅保留一份，删除重复定义）
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))

# 第十一步：404错误处理（放在视图函数最后）
@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('404.html', user=user), 404

# 第十二步：运行应用（程序入口，放在最后）
if __name__ == '__main__':
    app.run(debug=True)