# ======== import ==========
import http.client, json, subprocess, time, schedule, configparser
from telegram.ext import Updater, CommandHandler
from multiprocessing import Process

# ======== Подгрузка данных из конфига ==========

config = configparser.ConfigParser()
config.sections()
configFilePath = r'config.cfg'
config.read(configFilePath)
#config.sections('main')

bot_token = config.get('main', 'bot_token') #токен бота
path = config.get('main', 'path') #путь к майнеру
chat_id = config.get('main', 'chat_id') #chat_id

# ======== Global settings ==========

global_status = False #Статус сервера True - запущен. False - не запущен или процес помер.
restart_flag = True #Sucessfull restart flag for alert
pid = 0 # ПИД процесса майнера
delay = 30 # время сколько ждем после старта
updater = Updater(token=bot_token) #запуск экземпляра бота

# ======== start\kill miner functions ==========

def miner_start():  # запуска майнер
    pid = subprocess.Popen(path)
    print('miner started')
    return pid

def miner_kill():
    subprocess.Popen.terminate(pid)
    print('miner killed')

# ======== health check ==========

def health_check():
    global global_status, pid, restart_flag
    print('health check ',global_status)
    check_server()
    print(global_status)
    if global_status == False:
        updater.bot.send_message(chat_id=chat_id, text="Miner crashed. Restart attempt.")
        miner_kill()
        pid = miner_start()
        time.sleep(delay)
        global_status = True
        restart_flag = False
    else:
        if restart_flag == False:
            updater.bot.send_message(chat_id=chat_id, text="Miner successfully restarted.")
            restart_flag = True

#========= Data parsing from EWBF api ==========

def data_parsing():

    conn = http.client.HTTPConnection("127.0.0.1:42000")  # connect
    conn.request("GET", "/getstat")
    r1 = conn.getresponse()
    data = r1.read()  # data string with current status
    j1 = json.loads(data)  # грузим в формате json
    return j1


# ======== SERVER CHECK FUNC ==========


def check_server():

    global global_status
    response = ''  # final response
    total_sol = 0  # total sols

    try:    ## ======== connect to HTTP ==========
        j1 = data_parsing()  # trying to get updated from EWBF api
    except ConnectionRefusedError:
        updater.bot.send_message(chat_id=chat_id, text="Can't connect to miner API")
        global_status = False
        return

    # j1 = json.loads('{"method":"getstat", "error":null, "start_time":1518366545, "current_server":"eu1-zcash.flypool.org:3333", "available_servers":1, "server_status":2, "result":[{"gpuid":0, "cudaid":0, "busid":"0000:01:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":56, "gpu_power_usage":0, "speed_sps":168, "accepted_shares":2, "rejected_shares":1, "start_time":1518366546},{"gpuid":1, "cudaid":1, "busid":"0000:02:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":55, "gpu_power_usage":0, "speed_sps":188, "accepted_shares":4, "rejected_shares":0, "start_time":1518366546},{"gpuid":2, "cudaid":2, "busid":"0000:03:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":54, "gpu_power_usage":0, "speed_sps":181, "accepted_shares":0, "rejected_shares":0, "start_time":1518366546},{"gpuid":3, "cudaid":3, "busid":"0000:04:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":55, "gpu_power_usage":0, "speed_sps":182, "accepted_shares":2, "rejected_shares":0, "start_time":1518366546},{"gpuid":4, "cudaid":4, "busid":"0000:05:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":54, "gpu_power_usage":0, "speed_sps":184, "accepted_shares":2, "rejected_shares":1, "start_time":1518366546},{"gpuid":5, "cudaid":5, "busid":"0000:06:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":56, "gpu_power_usage":0, "speed_sps":180, "accepted_shares":1, "rejected_shares":0, "start_time":1518366547}]}')

    # ======== response creating ==========

    for i in range(len(j1["result"])):

        if j1["result"][i]["speed_sps"] == 0:
            response = response + '❌ '
        elif j1["result"][i]["speed_sps"] < 150:
            response = response + '⚠️ '
        else:
            response = response + '✅ '

        response = response + str(j1["result"][i]["gpuid"]) + ' | t°= ' + str(j1["result"][i]["temperature"]) + ' | ' + str(
            j1["result"][i]["speed_sps"]) + ' sol' + '\r\n'

        total_sol = total_sol + j1["result"][i]["speed_sps"]

    response = response + 'Total sol=' + str(total_sol)

    if total_sol == 0:
        global_status = False  # помечаем что сервак упал

    print('sols', total_sol)
    return response

# ======== The end of server check ==========

#========= Telegram bot ==========

def telegram_bot():
    #updater = Updater(token=bot_token)

    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Mininig bot")

# ==========stat func======================

    def statistics(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=check_server())

    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)

    statistics_handler = CommandHandler('stat', statistics)
    updater.dispatcher.add_handler(statistics_handler)

    updater.start_polling()
    updater.idle()


# ==========job schedule======================

def scheduler():

    global global_status
    global pid
    pid = miner_start()  # запуск майнера
    updater.bot.send_message(chat_id=chat_id, text="Miner started")
    global_status = True
    time.sleep(delay)  # ждем после первого запуска дабы healt check не сработал
    schedule.every(30).seconds.do(health_check)

    while True:
        schedule.run_pending()
        time.sleep(1)

#============ program MAIN ===================

if __name__ == '__main__':  #было бы не плохо разобраться как эта штука работает
    thread1 = Process(target=telegram_bot)
    thread1.start()

    thread2 = Process(target=scheduler)
    thread2.start()
