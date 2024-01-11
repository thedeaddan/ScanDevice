import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from peewee import AutoField, CharField, Model, IntegerField, SqliteDatabase,FloatField

url = "https://technical.city/en/cpu/rating"

db = SqliteDatabase('databases/accessories.db')

class CPUs(Model):
    rating_position = IntegerField(unique=True)
    name = CharField()
    socket = CharField()
    cores_threads = CharField()
    base_frequency = FloatField()
    max_memory = CharField()
    price = IntegerField()
    TDP = IntegerField()

    class Meta:
        database = db

db.connect()
db.create_tables([CPUs], safe=True)

# Инициализация драйвера Selenium
driver = webdriver.Chrome()

# Загрузка страницы
driver.get(url)

# Ждем, чтобы динамический контент успел загрузиться
time.sleep(5)

# Листаем страницу до конца
# Скроллим вниз с помощью JavaScript
for i in range(0,30):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Ждем загрузки дополнительных данных
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
new_rows = soup.find_all("tr", {"data-id": True})

# Проходимся по новым строкам и извлекаем данные для CPU
data_list = []
for row in new_rows:
    rating_position = int(row.find("td", class_="rating_list_position").text.strip())
    cpu_name = row.find_all("td")[1].find("img")["alt"] if row.find_all("td")[1].find("img") else "N/A"
    socket = row.find_all("td")[3].text.strip()
    base_frequency = float(row.find_all("td")[4].text.strip())
    cores_threads = row.find_all("td")[5].text.strip()
    max_memory = row.find_all("td")[6].text.strip()

    # Проверяем, может ли price быть преобразован в int
    try:
        price = int(row.find_all("td")[7].text.strip().split(" ")[0])
    except ValueError:
        price = 0

    # Проверяем, может ли power быть преобразован в int
    try:
        power_consumption = int(row.find_all("td")[8].text.strip().split(" ")[0]) if row.find_all("td")[8].text.strip() else 0
    except ValueError:
        power_consumption = 0

    # Проверяем, есть ли уже запись с таким rating_position
    existing_record = CPUs.select().where(CPUs.rating_position == rating_position).first()

    # Если нет, добавляем данные в список словарей
    if not existing_record:
        data_list.append({
            "rating_position": rating_position,
            "name": cpu_name,
            "socket": socket,
            "base_frequency": base_frequency,
            "cores_threads": cores_threads,
            "max_memory": max_memory,
            "price": price,
            "TDP": power_consumption
        })
        print(data_list[-1])

# Вставляем только уникальные записи в базу данных
if data_list:
    CPUs.insert_many(data_list).execute()

# Закрываем драйвер после использования
driver.quit()
