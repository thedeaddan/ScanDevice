from peewee import SqliteDatabase, AutoField, CharField, Model
from psutil import virtual_memory, cpu_count, cpu_freq
from telebot import telebot
from platform import system,uname,processor,machine
print("Инициализация токена...")
try:
    from config import token, user_id
    bot = telebot.TeleBot(token=token)
except Exception as e:
    print(f"Ошибка инициализации бота: {e}")

print("Инициализация базы данных SQLite...")
db = SqliteDatabase('computer_info.db')

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

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def bytes_to_gb(bytes_value):
    return round(bytes_value / (1024 ** 3))

print("Создание таблицы, если она еще не существует...")
db.connect()
db.create_tables([ComputerInfo], safe=True)

print("Сбор информации о системе...")
if system() == "Linux":
    import GPUtil
    gpu = GPUtil.getGPUs()[0]
    uname = uname()
    processor_name = uname.processor
    node_name = uname.node
    processor_cores = cpu_count(logical=False)
    processor_threads = cpu_count(logical=True)
    svmem = virtual_memory()
    ram = get_size(svmem.total)
    graphics_card_mem = f"{gpu.memoryTotal}MB"
    graphics_card = gpu.name
    os_name = uname.system
    os_version = uname.version
else:
    from wmi import WMI
    computer = WMI()
    computer_info = computer.Win32_ComputerSystem()[0]
    os_info = computer.Win32_OperatingSystem()[0]
    proc_info = computer.Win32_Processor()[0]
    gpu_info = computer.Win32_VideoController()[0]
    disk_info = computer.Win32_DiskDrive()

    processor_name = proc_info.Name
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