from wmi import WMI
from peewee import SqliteDatabase, AutoField, CharField, Model
from telebot import telebot
import GPUtil
from config import token,user_id
import psutil
import platform

print("Инициализация токена...")
try:
    bot = telebot.TeleBot(token=token)
except:
    print("Не удалось иницилизировать бота, отправки сообщений не будет")

print("Инициализация базы данных SQLite...")
db = SqliteDatabase('computer_info.db')


def get_size(bytes, suffix="B"):
    print(f"Преобразование размера в удобочитаемый формат для {bytes}...")
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


class ComputerInfo(Model):
    computer_id = AutoField()
    node_name = CharField()
    processor_name = CharField()
    processor_cores = CharField()
    processor_threads = CharField()
    ram = CharField()
    graphics_card = CharField()
    graphics_card_mem = CharField()
    os_name = CharField()
    os_version = CharField()
    hard_drive = CharField()

    class Meta:
        database = db


print("Создание таблицы, если она еще не существует...")
db.connect()
db.create_tables([ComputerInfo], safe=True)

print("Инициализация WMI...")
computer = WMI()
print("Сбор информации о системе...")
computer_info = computer.Win32_ComputerSystem()[0]
node_name = platform.uname().node
print(f"Имя компьютера: {node_name}\n")
os_info = computer.Win32_OperatingSystem()[0]
proc_info = computer.Win32_Processor()[0]
gpu_info = computer.Win32_VideoController()[0]
disk_info = computer.Win32_DiskDrive()

processor_name = proc_info.Name
print(f"Процессор: {processor_name}")
processor_cores = str(psutil.cpu_count(logical=False))
print(f"Количество ядер: {processor_cores}")
processor_threads = str(psutil.cpu_count(logical=True))
print(f"Количество потоков: {processor_threads}")
svmem = psutil.virtual_memory()
ram = f"{get_size(svmem.total)}"
print(f"ОЗУ: {ram}")

gpu = GPUtil.getGPUs()[0]
graphics_card = gpu_info.Name
print(f"Видеокарта: {graphics_card}")
graphics_card_mem = f"{gpu.memoryTotal} MB"
print(f"Видеопамять: {graphics_card_mem}")

os_name = os_info.Name.encode('utf-8').split(b'|')[0].decode('utf-8')
os_version = f"{os_info.Version} {os_info.BuildNumber}"
print(f"ОС: {os_name} {os_version}")
hard_drives = [f"{get_size(float(disk.Size))}" for disk in disk_info]
print(f"Жесткие диски: {', '.join(hard_drives)}")

print("Сохранение информации в базе данных...")
ComputerInfo.create(
    node_name = node_name,
    processor_name=processor_name,
    processor_cores=processor_cores,
    processor_threads=processor_threads,
    ram=ram,
    graphics_card=graphics_card,
    graphics_card_mem = graphics_card_mem,
    os_name=os_name,
    os_version=os_version,
    hard_drive=', '.join(hard_drives)
)

print("Сохранение информации в текстовый файл...")
with open('computer_info.txt', 'a', encoding='utf-8') as file:
    file.write("\n\n===== ID компьютера: {} =====\n".format(ComputerInfo.select().order_by(ComputerInfo.computer_id.desc()).limit(1).get().computer_id))
    file.write(f"Имя компьютера: {node_name}\n")
    file.write("ОС: " + os_name + " " + os_version + "\n")
    file.write("Процессор: " + processor_name + "\n")
    file.write("Количество ядер: " + processor_cores + "\n")
    file.write("Количество потоков: " + processor_threads + "\n")
    file.write("ОЗУ: " + ram + "\n")
    file.write("Видеокарта: " + graphics_card + "\n")
    file.write("Видеопамять: "+graphics_card_mem+"\n")
    file.write("Жесткие диски: " + ', '.join(hard_drives) + "\n")

text = ""
text += ("\n\n===== ID компьютера: {} =====\n".format(ComputerInfo.select().order_by(ComputerInfo.computer_id.desc()).limit(1).get().computer_id))
text += (f"Имя компьютера: {node_name}\n")
text += ("ОС: " + os_name + " " + os_version + "\n")
text += ("Процессор: " + processor_name + "\n")
text += ("Количество ядер: " + processor_cores + "\n")
text += ("Количество потоков: " + processor_threads + "\n")
text += ("ОЗУ: " + ram + "\n")
text += ("Видеокарта: " + graphics_card + "\n")
text += ("Видеопамять: "+graphics_card_mem+"\n")
text += ("Жесткие диски: " + ', '.join(hard_drives) + "\n")

print("Отправка сообщения через Telegram...")
if bot:
    bot.send_message(user_id, "*Был просканирован новый компьютер!*", parse_mode="Markdown")
    bot.send_message(user_id, text)
else:
    print("Бот не иницилизирован, отправка отменена")
print("Процесс завершен.")
input("Нажмите для выхода")
