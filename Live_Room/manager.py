# -*- coding:utf—8 -*-
# python源程序 todo
# 作者：liuwei
# 备注：未经本人允许 请勿盗窃   http://www.baidu.com
from ihome import creat_config, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
# 建立flask对象
app = creat_config("development")

# 配置数据库脚本方法
manager = Manager(app)

Migrate(app, db)
manager.add_command("db", MigrateCommand)



if __name__ == '__main__':
    manager.run()
