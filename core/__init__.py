try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # Local environments with mysqlclient can continue using that driver.
    pass
