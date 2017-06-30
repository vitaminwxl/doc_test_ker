judy 文档
==============================================

安装方法
-----------------------------------------------
### 
tar -zxf pip-8.1.1.tar.gz

python setup.py install

yum install mysql mysql-devel

yum install python-ldap

pip install -r requirements.txt


git clone http://username:password @10.125.211.3:21908/devops/judy.git

在10.125.211.2数据库操作

grant all on judy.* to judy@'10.125.110.11' identified by 'D1bo7laTvLbUqepzH9et';

 
启动
-----------------------------------------------
### 
python manage.py runserver 0.0.0.0:3311

python manage.py rqworker high default low

zeus需要启动10.125.211.2上的3344端口
