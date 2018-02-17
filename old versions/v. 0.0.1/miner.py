# ======== Global settings ==========

#bot_token = '508704594:AAFQUpN9KUIdYaIxP42EPKsDM-VGO7MpIQI' #продуктовый бот
bot_token = '500993427:AAG7_wtQ6Yal6KaAfnpug9HNsSXthen_ixM' #тестовый бот
#путь до майнера + флаги запуска
path=r'C:\Users\Vanipel\Desktop\0.3.4b\miner.exe --intensity 1 --server eu1-zcash.flypool.org --user t1R5KwDBPtDxVxvEyTb1KBF26tKKN4eWhxC.vanipel --pass x --port 3333 --log 2 --api'
global_status = False #Статус сервера True - запущен. False - не запущен или процес помер.
pid = 0 # ПИД процесса майнера
delay = 30 # время сколько ждем после старта

# ======== import ==========
import http.client, json, subprocess, time, schedule
from telegram.ext import Updater, CommandHandler
from multiprocessing import Process

# ======== start\kill miner functions ==========

def miner_start():  # запуска майнер
    pid = subprocess.Popen(path)
    print('miner started')
    return pid

def miner_kill():
    subprocess.Popen.terminate(pid)
    print('miner killed')

# ======== set global status true ==========
#def status_refresh():

#global_status
# ======== health check ==========

def health_check():
    global global_status
    print('health check ',global_status)
    check_server()
    if global_status == False:
        miner_kill()
        pid = miner_start()
        time.sleep(delay)
        global_status = True

# ======== SERVER CHECK FUNC ==========
def check_server():
    # ======== connect to HTTP ==========

    conn = http.client.HTTPConnection("127.0.0.1:42000")  # connect
    conn.request("GET", "/getstat")
    r1 = conn.getresponse()
    data = r1.read()  # data string with current status

    # ======== JSON import ==========

    j1 = json.loads(data)  # грузим в формате json
    # j1 = json.loads('{"method":"getstat", "error":null, "start_time":1518366545, "current_server":"eu1-zcash.flypool.org:3333", "available_servers":1, "server_status":2, "result":[{"gpuid":0, "cudaid":0, "busid":"0000:01:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":56, "gpu_power_usage":0, "speed_sps":168, "accepted_shares":2, "rejected_shares":1, "start_time":1518366546},{"gpuid":1, "cudaid":1, "busid":"0000:02:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":55, "gpu_power_usage":0, "speed_sps":188, "accepted_shares":4, "rejected_shares":0, "start_time":1518366546},{"gpuid":2, "cudaid":2, "busid":"0000:03:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":54, "gpu_power_usage":0, "speed_sps":181, "accepted_shares":0, "rejected_shares":0, "start_time":1518366546},{"gpuid":3, "cudaid":3, "busid":"0000:04:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":55, "gpu_power_usage":0, "speed_sps":182, "accepted_shares":2, "rejected_shares":0, "start_time":1518366546},{"gpuid":4, "cudaid":4, "busid":"0000:05:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":54, "gpu_power_usage":0, "speed_sps":184, "accepted_shares":2, "rejected_shares":1, "start_time":1518366546},{"gpuid":5, "cudaid":5, "busid":"0000:06:00.0", "name":"GeForce GTX 1050 Ti", "gpu_status":2, "solver":0, "temperature":56, "gpu_power_usage":0, "speed_sps":180, "accepted_shares":1, "rejected_shares":0, "start_time":1518366547}]}')

    # ======== response creating ==========
    global global_status
    response = ''  # final response
    total_sol = 0  # total sols

    for i in range(len(j1["result"])):
        response = response + 'GPU_id=' + str(j1["result"][i]["gpuid"]) + ' status=' + str(
            j1["result"][i]["gpu_status"]) + ' temp= ' + str(j1["result"][i]["temperature"]) + ' speed= ' + str(
            j1["result"][i]["speed_sps"]) + '\r\n'
        total_sol = total_sol + j1["result"][i]["speed_sps"]

    response = response + 'total sol=' + str(total_sol)

    if total_sol == 0:
        response = response + '❌'
        global_status = False  # помечаем что сервак упал
    else:
        response = response + '✅'
    print('sols', total_sol)
    return response

"""
# ======== The end of server check ==========

#print(check_server())
"""

#========= Telegram bot ==========

#import logging

def telegram_bot():
    updater = Updater(token=bot_token)


#bot.send_message(chat_id=-265554557, text="I'm sorry Dave I'm afraid I can't do that.")

# dispatcher = updater.dispatcher

# логирование
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="bot for rig")


    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)


# ==========stat func======================

    def statistics(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text=check_server())


    statistics_handler = CommandHandler('stat', statistics)
    updater.dispatcher.add_handler(statistics_handler)

    updater.start_polling()
    updater.idle()

# ==========job schedule======================

def scheduler():
    global global_status
    global pid
    pid = miner_start()  # запуск майнера
    global_status = True
    time.sleep(delay)  # ждем после первого запуска дабы healt check не сработал
    schedule.every(10).seconds.do(health_check)

    while True:
        schedule.run_pending()
        time.sleep(1)

#============ program MAIN ===================


if __name__ == '__main__':  #было бы не плохо разобраться как эта штука работает
    thread1 = Process(target=telegram_bot)
    thread1.start()

    thread2 = Process(target=scheduler)
    thread2.start()
    #proc.join()
