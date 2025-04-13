from models.database import Database

# Создаем экземпляр класса Database
db = Database()

# Проверяем, что таблица стран создана и заполнена
db.create_tables()
db.insert_default_countries()

# Получаем список стран
countries = db.get_countries()
print(f"Количество стран в базе данных: {len(countries)}")

# Получаем страну по коду
country = db.get_country_by_code('RU')
if country:
    print(f"Страна с кодом 'RU': {country.name}")
else:
    print("Страна с кодом 'RU' не найдена") 