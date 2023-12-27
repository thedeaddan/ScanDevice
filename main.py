import sys
from peewee import SqliteDatabase, AutoField, CharField, Model
from telebot import telebot
from psutil import virtual_memory, cpu_count, disk_partitions, disk_usage

# Проверка операционной системы
if sys.platform.startswith('linux'):
    from psutil import cpu_freq
else:
    from wmi import WMI

print("Инициализация токена...")
try:
    from config import token, user_id
    bot = telebot.TeleBot(token=token)
except Exception as e:
    print(f"Ошибка инициализации бота: {e}")

print("Инициализация базы данных SQLite...")
db = SqliteDatabase('computer_info.db')


def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3))

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

print("Сбор информации о системе...")
if sys.platform.startswith('linux'):
    node_name = 'Linux Machine'  # Примерное имя узла
    os_name = 'Linux'
    os_version = sys.platform
    with open('/proc/cpuinfo', 'r') as f:
        for line in f.readlines():
            if 'model name' in line:
                processor_name = line.split(':')[1].strip()
                break
        else:
            processor_name = 'Unknown Processor'
    processor_cores = str(cpu_count(logical=False))
    processor_threads = str(cpu_count(logical=True))
    svmem = virtual_memory()
    ram = get_size(svmem.total)
    disk = disk_partitions()[0].mountpoint
    hard_drives = [f"{get_size(disk_usage(disk).total)} ({disk})"]

    # Дополнительная информация для Linux
    #os_version = ' '.join([part for part in open('/etc/os-release').readlines() if part.startswith('PRETTY_NAME')][0].split('=')[1].strip('"')])

else:
    computer = WMI()
    computer_info = computer.Win32_ComputerSystem()[0]
    os_info = computer.Win32_OperatingSystem()[0]
    proc_info = computer.Win32_Processor()[0]
    gpu_info = computer.Win32_VideoController()[0]
    disk_info = computer.Win32_DiskDrive()

node_name = os_info.CSName
processor_cores = str(cpu_count(logical=False))
processor_threads = str(cpu_count(logical=True))
svmem = virtual_memory()
ram = get_size(svmem.total)
graphics_card_mem = bytes_to_gb(int(str(gpu_info).split("AdapterRAM")[1].split(";")[0].split(" ")[2]))
graphics_card = gpu_info.Name

os_name = os_info.Name.encode('utf-8').split(b'|')[0].decode('utf-8')
os_version = f"{os_info.Version} {os_info.BuildNumber}"

hard_drives = [get_size(float(disk.Size)) for disk in disk_info]

ComputerInfo.create(
    node_name=node_name,
    processor_name=processor_name,
    processor_cores=processor_cores,
    processor_threads=processor_threads,
    ram=ram,
    graphics_card=graphics_card,
    graphics_card_mem=graphics_card_mem,
    os_name=os_name,
    os_version=os_version,
    hard_drive=', '.join(hard_drives)
)

text = (f"\n\n===== ID компьютера: {ComputerInfo.select().order_by(ComputerInfo.computer_id.desc()).limit(1).get().computer_id} =====\n"
        f"Имя компьютера: {node_name}\n"
        f"ОС: {os_name} {os_version}\n"
        f"Процессор: {processor_name}\n"
        f"Количество ядер: {processor_cores}\n"
        f"Количество потоков: {processor_threads}\n"
        f"ОЗУ: {ram}\n"
        f"Видеокарта: {graphics_card}\n"
        f"Видеопамять: {graphics_card_mem}GB\n"
        f"Жесткие диски: {', '.join(hard_drives)}\n")

print("Сохранение информации в текстовый файл...")
with open('computer_info.txt', 'a', encoding='utf-8') as file:
    file.write(text)

print("Отправка сообщения через Telegram...")
if bot:
    try:
        bot.send_message(user_id, "*Был просканирован новый компьютер!*", parse_mode="Markdown")
        bot.send_message(user_id, text)
    except Exception as e:
        print(f"Ошибка отправки сообщения в Telegram: {e}")
else:
    print("Бот не инициализирован, отправка отменена")

print("Процесс завершен.")
input("Нажмите для выхода")
