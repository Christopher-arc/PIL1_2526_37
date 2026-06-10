from flask_mysqldb import MySQL

mysql = MySQL()

def init_db(app):
    app.config['MYSQL_HOST']        = 'localhost'
    app.config['MYSQL_USER']        = 'root'
    app.config['MYSQL_PASSWORD']    = '1234'
    app.config['MYSQL_DB']          = 'IFRI_MentorLink'
    app.config['MYSQL_PORT']        = 3307
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    mysql.init_app(app)