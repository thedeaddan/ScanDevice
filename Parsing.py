import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from peewee import AutoField, CharField, Model, IntegerField, SqliteDatabase

url = "https://technical.city/en/video/rating"

db = SqliteDatabase('databases/accessories.db')

class VideoCards(Model):
    rating_position = IntegerField(unique=True)  # Устанавливаем уникальность для поля rating_position
    name = CharField()
    price = IntegerField()
    TDP = IntegerField()

    class Meta:
        database = db

db.connect()
db.create_tables([VideoCards], safe=True)

# Инициализация драйвера Selenium
driver = webdriver.Chrome()

# Загрузка страницы
driver.get(url)

# Ждем, чтобы динамический контент успел загрузиться
time.sleep(5)

# Скроллим вниз с помощью JavaScript
for i in range(0,10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Ждем загрузки дополнительных данных
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
new_rows = soup.find_all("tr", {"data-id": True})

# Проходимся по новым строкам и извлекаем данные
data_list = []
for row in new_rows:
    rating_position = int(row.find("td", class_="rating_list_position").text.strip())
    video_card_name = row.find_all("td")[1].find("img")["alt"] if row.find_all("td")[1].find("img") else "N/A"
    price = row.find_all("td")[6].text.strip()
    try:
        price = int(price.split(" ")[0])
    except:
        price = 0
    power_consumption = row.find_all("td")[7].text.strip().split(" ")[0] if row.find_all("td")[7].text.strip() else None
    try:
        power_consumption = int(power_consumption.replace(".",","))
    except:
        power_consumption = 0
    # Проверяем, есть ли уже запись с таким rating_position
    existing_record = VideoCards.select().where(VideoCards.rating_position == rating_position).first()

    # Если нет, добавляем данные в список словарей
    if not existing_record:
        data_list.append({
            "rating_position": rating_position,
            "name": video_card_name,
            "price": price,
            "TDP": power_consumption
        })


# Вставляем только уникальные записи в базу данных
VideoCards.insert_many(data_list).execute()

# Закрываем драйвер после использования
driver.quit()
