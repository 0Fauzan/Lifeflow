import os

# Only use PyMySQL for local MySQL — skip on Render (PostgreSQL)
if not os.environ.get('DATABASE_URL'):
    import pymysql
    pymysql.install_as_MySQLdb()
