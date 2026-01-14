from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'hello world'

@app.route('/register', methods=['GET', 'POST'])  # 接受GET和POST方法
def register():
    # 修正点1：所有print添加括号，适配Python3语法
    print(request.headers)  # 打印请求头
    print(request.form)     # 打印所有表单数据
    print(request.form.get('name'))  # 安全获取name字段（推荐，无字段返回None）
    print(request.form.get('name'))  # 重复打印仅为对齐原代码，可删除
    print(request.form.getlist('name'))  # 获取多值表单字段（如同名多个输入）
    print(request.form.get('nickname', default='little apple'))  # 带默认值的安全获取
    
    # 原代码直接使用request.form['name']存在风险，已替换为get()方法避免KeyError
    return 'welcome'

if __name__ == '__main__':
    app.run(debug=True)