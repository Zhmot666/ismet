import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute('SELECT * FROM connections WHERE is_active = 1')
print('Активное подключение:')
result = c.fetchone()
print(result)

c.execute('SELECT * FROM credentials')
print('\nУчетные данные:')
for row in c.fetchall():
    print(row)

conn.close() 