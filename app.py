from flask import Flask, url_for, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy 

# 移除冗余导入（sys、os、psycopg2，无需再适配SQLite路径）

app = Flask(__name__)

# 1. 保留SECRET_KEY，支持flash()和session功能
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 生产环境使用secrets.token_hex(16)生成随机字符串

# 2. 配置MySQL数据库连接（核心：不使用pymysql，依赖mysqlclient驱动）
# 连接格式：mysql://[用户名]:[密码]@[主机地址]:[端口]/[数据库名]?charset=utf8mb4
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost:3306/flask_movie_db?charset=utf8mb4'
# 解释：
# - root：MySQL用户名（可替换为你的自定义用户名，如user）
# - your_mysql_password：MySQL用户密码（替换为你的实际MySQL密码，不能为空请填写）
# - localhost：MySQL主机地址（本地服务填localhost，远程服务填对应IP）
# - 3306：MySQL默认端口（未修改则保持不变）
# - flask_movie_db：步骤1中创建的MySQL数据库名（需与实际创建的一致）

# 3. 关闭模型修改监控，提升性能
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化SQLAlchemy（关联Flask应用）
db = SQLAlchemy(app)

# 定义数据模型（与之前一致，无需修改，SQLAlchemy自动适配MySQL表结构）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键，MySQL自动支持自增
    name = db.Column(db.String(20))  # 对应MySQL的VARCHAR(20)


@app.context_processor
def inject_user():
    user = User.query.first()  # 从数据库查询包含 name 的 user 对象
    return dict(user=user)  # 传递给模板，模板中可通过 {{ user.name }} 访问

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))  # 对应MySQL的VARCHAR(60)
    year = db.Column(db.String(4))  # 对应MySQL的VARCHAR(4)

# 4. 初始化数据库表和默认数据（应用上下文内执行）
with app.app_context():
    # 创建所有数据表（若表已存在，不会重复创建，安全执行）
    db.create_all()
    # 初始化默认用户数据（避免User.query.first()返回None）
    if not User.query.first():
        user = User(name='Zhang Qi')
        db.session.add(user)
        db.session.commit()

# 5. 主页视图函数（逻辑与之前一致，无需修改）
@app.route('/',methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取表单数据
        title = request.form.get('title')
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('index'))
        # 保存到MySQL数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    user = User.query.first()
    movies = Movie.query.all()
    return render_template('index.html', user=user, movies=movies)

# 6. 404错误处理（逻辑不变）
@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('404.html', user=user), 404

@app.route('/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    # 1. 正确查询 movie 对象，不存在则返回 404
    movie = Movie.query.get_or_404(movie_id)
    
    # 2. POST 请求处理（数据更新，可选，不影响变量传递）
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
    
    # 3. 关键：将 movie 变量传递给 edit.html（变量名 movie 与 HTML 中一致）
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

if __name__ == '__main__':
    app.run(debug=True)