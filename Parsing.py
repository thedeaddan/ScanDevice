import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from peewee import AutoField, CharField, Model, IntegerField, SqliteDatabase

url = "https://technical.city/en/video/best-price-to-performance"

db = SqliteDatabase('computer_info.db')

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

# Листаем страницу до конца или до тех пор, пока не найдем rating_position 827
while True:
    # Скроллим вниз с помощью JavaScript
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
        price = int(row.find_all("td")[6].text.strip().split(" ")[0])
        power_consumption = row.find_all("td")[7].text.strip().split(" ")[0] if row.find_all("td")[7].text.strip() else None
        try:
            power_consumption = int(power_consumption.replace(".",","))
        except:
            power_consumption = None
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

        # Если найден rating_position 827, завершаем цикл
        if rating_position == 827:
            break

    # Если rating_position 827 был найден, выходим из внешнего цикла
    if rating_position == 827:
        break

    # Вставляем только уникальные записи в базу данных
    VideoCards.insert_many(data_list).execute()

# Закрываем драйвер после использования
driver.quit()
