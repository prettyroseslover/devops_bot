import logging, re, os, paramiko, shlex

import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from dotenv import load_dotenv
load_dotenv()


TOKEN=os.getenv('TOKEN')


logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Ciao, {user.full_name}!')


def helpCommand(update: Update, context):
    help = ["/help -- помощь",
            "/find_email -- найти email в тексте и добавить в БД",
            "/find_phone_number -- найти номера телефонов в тексте и добавить в БД",
            "/get_emails -- получить список email из БД",
            "/get_phone_numbers -- получить список номеров телефонов из БД",
            "/get_repl_logs -- логи репликации",
            "/verify_password -- проверить сложность пароля",
            "/get_release -- информация о релизе",
            "/get_uname -- архитектура, имя хоста, версия ядра",
            "/get_uptime -- время работы",
            "/get_df -- состояние файловой системы",
            "/get_free -- свободная память",
            "/get_mpstat -- производительность системы",
            "/get_w -- работющие в системе пользователи",
            "/get_auths -- последние 10 входов в систему",
            "/get_critical -- последние 5 критических события",
            "/get_ps -- запущенные процессы",
            "/get_ss -- используемые порты",
            "/get_apt_list -- без аргументов - установленные пакеты\nс аргументом - поиск пакета (если есть)",
            "/get_services -- информация о запущенных сервисах",
            ]
    
    result = "\n".join(help)

    update.message.reply_text(result)


def releaseCommand(update: Update, context):
    cmd = "uname -r"
    update.message.reply_text(sshCommand(cmd))


def unameCommand(update: Update, context):
    cmd = "uname -m -n -v"
    update.message.reply_text(sshCommand(cmd))


def uptimeCommand(update: Update, context):
    cmd = "uptime --pretty"
    update.message.reply_text(sshCommand(cmd))


def dfCommand(update: Update, context):
    cmd = "df"
    update.message.reply_text(sshCommand(cmd))


def freeCommand(update: Update, context):
    cmd = "free"
    update.message.reply_text(sshCommand(cmd))


def mpstatCommand(update: Update, context):
    cmd = "mpstat"
    update.message.reply_text(sshCommand(cmd))


def wCommand(update: Update, context):
    cmd = "w"
    update.message.reply_text(sshCommand(cmd))

def authsCommand(update: Update, context):
    cmd = "last -n 10"
    update.message.reply_text(sshCommand(cmd))


def criticalCommand(update: Update, context):
    cmd = "journalctl -p 2 -n 5"
    result = sshCommand(cmd)
    if result == '':
        update.message.reply_text("Таких событий нет")
    else:
        update.message.reply_text(result)

def psCommand(update: Update, context):
    cmd = "ps -e | head -n 10"
    update.message.reply_text(sshCommand(cmd))

def ssCommand(update: Update, context):
    cmd = "ss | head -n 20 |  awk \'{print $1\"\t\"$2\"\t\"$5\"\t\"$6}\'"
    update.message.reply_text(sshCommand(cmd))


def aptlistCommand(update: Update, context):
    if not context.args:
        cmd = "dpkg -l | tail -n +6 | head -n 15"
        update.message.reply_text(sshCommand(cmd))
    else:
        safe_command = shlex.quote(context.args[0])
        cmd = f"dpkg -S {safe_command}"
        result = sshCommand(cmd)
        if result == '':
            update.message.reply_text("Искомое не найдено!")
        else:
            update.message.reply_text(result)


def servicesCommand(update: Update, context):
    cmd = "systemctl list-units --state=active --type=service --no-legend | awk '{print $1}'"
    update.message.reply_text(sshCommand(cmd))

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'


def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    pattern = r'((8|\+7) \(\d{3}\) \d{3}-\d{2}-\d{2}|(8|\+7)-\d{3}-\d{3}-\d{2}-\d{2}|(8|\+7) \d{3} \d{3} \d{2} \d{2}|(8|\+7) \(\d{3}\) \d{3} \d{2} \d{2}|(8|\+7)\d{10}|(8|\+7)\(\d{3}\)\d{7})'

    phoneNumRegex = re.compile(pattern) 

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END 
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i][0]}\n' # Записываем очередной номер
        
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    update.message.reply_text('Желаете записать их в базу данных? Для отказа напишите нет!')
    context.user_data["numbers"] = phoneNumberList
    return 'savePhoneNumbers'


def savePhoneNumbers(update: Update, context):
    user_input = update.message.text 
    if user_input.lower() == "нет":
        update.message.reply_text('Жаль :(')
        return ConversationHandler.END
    else:
        connection = connect_to_db()
        if connection == None:
            update.message.reply_text("Не удалось подключиться к БД")
            return ConversationHandler.END
        else:
            cursor = connection.cursor()
            for num in context.user_data["numbers"]:
                cursor.execute("INSERT INTO phonenumbers (phone) VALUES (%s)", (num[0], ))
                connection.commit()
            cursor.close()
            connection.close()
            update.message.reply_text("Запись закончена!")
        return ConversationHandler.END


def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')

    return 'findEmails'


def findEmails (update: Update, context):
    user_input = update.message.text 

    pattern = r'([a-zA-Z0-9.!#$%&’*+=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*)'

    emailRegex = re.compile(pattern) 

    emailList = emailRegex.findall(user_input) 

    if not emailList: 
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    
    emails = '' 
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' 
        
    update.message.reply_text(emails)
    update.message.reply_text('Желаете записать их в базу данных? Для отказа напишите нет!')
    context.user_data["emails"] = emailList

    return 'saveEmails'


def saveEmails(update: Update, context):
    user_input = update.message.text 
    if user_input.lower() == "нет":
        update.message.reply_text('Жаль :(')
        return ConversationHandler.END
    else:
        connection = connect_to_db()
        if connection == None:
            update.message.reply_text("Не удалось подключиться к БД")
            return ConversationHandler.END
        else:
            cursor = connection.cursor()
            for email in context.user_data["emails"]:
                cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email, ))
                connection.commit()
            cursor.close()
            connection.close()
            update.message.reply_text("Запись закончена!")
        return ConversationHandler.END


def verifyPasswordCommand (update: Update, context):
    update.message.reply_text('Введите пароль для проверки его сложности: ')

    return 'verifyPassword'


def verifyPassword(update: Update, context):
    user_input = update.message.text
    pattern = r'^(?=.*[A-Z])(?=.*[!@#$%^&*()])(?=.*[0-9])(?=.*[a-z]).{8,}$'
    passwordRegex = re.compile(pattern) 

    mo = passwordRegex.search(user_input)
    if mo:
        update.message.reply_text("Пароль сложный") 
    else:
        update.message.reply_text("Пароль простой")
     
    return ConversationHandler.END 


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def connect_to_db():
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                  password=os.getenv('DB_PASSWORD'),
                                  host=os.getenv('DB_HOST'),
                                  port=os.getenv('DB_PORT'), 
                                  database=os.getenv('DB_DATABASE'))
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    
    return connection


def getEmailsCommand(update: Update, context):
    connection = connect_to_db()
    if connection == None:
        update.message.reply_text("Не удалось подключиться к БД")
    else:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        result = "\n".join(list(map(lambda row: row[1], data)))
        cursor.close()
        connection.close()
        update.message.reply_text(result)


def getPhoneNumbersCommand(update: Update, context):
    connection = connect_to_db()
    if connection == None:
        update.message.reply_text("Не удалось подключиться к БД")
    else:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phonenumbers;")
        data = cursor.fetchall()
        result = "\n".join(list(map(lambda row: row[1], data)))
        cursor.close()
        connection.close()
        update.message.reply_text(result)


def sshCommand(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=os.getenv('RM_HOST'),
                       username=os.getenv('RM_USER'),
                       password=os.getenv('RM_PASSWORD'),
                       port=os.getenv('RM_PORT'),
                       look_for_keys=False,
                       allow_agent=False)
    except:
        logging.error("Ошибка при подключении к удаленной машине")
        return "Не удалось подключиться к удаленной машине"
    _, stdout, _ = client.exec_command(cmd)
    data = stdout.read().decode("utf-8")
    client.close()
    return data



def getLogsCommand(update: Update, context):
    cmd = "cat /var/log/postgresql/postgresql-15-main.log | grep repl | tail -n 10"
    update.message.reply_text(sshCommand(cmd))


def main():

    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'savePhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, savePhoneNumbers)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'saveEmails': [MessageHandler(Filters.text & ~Filters.command, saveEmails)],
        },
        fallbacks=[]
    )

    convHandlerPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerPassword)

    # часть 3
    dp.add_handler(CommandHandler("get_release", releaseCommand))
    dp.add_handler(CommandHandler("get_uname", unameCommand))
    dp.add_handler(CommandHandler("get_uptime", uptimeCommand))
    dp.add_handler(CommandHandler("get_df", dfCommand))
    dp.add_handler(CommandHandler("get_free", freeCommand))
    dp.add_handler(CommandHandler("get_mpstat", mpstatCommand))
    dp.add_handler(CommandHandler("get_w", wCommand))
    dp.add_handler(CommandHandler("get_auths", authsCommand))
    dp.add_handler(CommandHandler("get_critical", criticalCommand))
    dp.add_handler(CommandHandler("get_ps", psCommand))
    dp.add_handler(CommandHandler("get_ss", ssCommand))
    dp.add_handler(CommandHandler("get_apt_list", aptlistCommand))
    dp.add_handler(CommandHandler("get_services", servicesCommand))

    # занятие 2, БД
    dp.add_handler(CommandHandler("get_emails", getEmailsCommand))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhoneNumbersCommand))
    dp.add_handler(CommandHandler("get_repl_logs", getLogsCommand))

	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()