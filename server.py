import socket
import sqlite3
import time
import threading
import json

def get_c_c():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = get_c_c()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nick TEXT,
    password TEXT,
    desc TEXT,
    IP TEXT,
    pc TEXT
)""")

clients = []

def handle_client(client_socket, client_address):
    try:
        print('Подключение от', client_address)

        while True:
            # Получаем данные от клиента
            data, addr = client_socket.recvfrom(1024)
            if not data:
                break
            print('Получено:', data.decode('UTF-8'))

            # Обрабатываем команду
            if data.decode('UTF-8') == "/c":
                response = 'ok'
                client_socket.sendto(response.encode('UTF-8'), client_address)

            elif data.decode('UTF-8').startswith("/acc_log_or_reg-=S=-"):
                com, pc = data.decode('UTF-8').split("-=S=-")
                conn, cursor = get_c_c()
                cursor.execute("SELECT nick FROM users WHERE pc = ?", (pc,))
                f = cursor.fetchone()
                if f is None:
                    response = "no"
                else:
                    response = "ok"
                client_socket.sendto(response.encode('UTF-8'), client_address)


            elif data.decode('UTF-8').startswith("/check"):
                com, n, p, pc = data.decode('UTF-8').split("-=S=-")
                conn, cursor = get_c_c()
                cursor.execute("SELECT nick FROM users WHERE nick=? AND password=?", (n, p,))
                res = cursor.fetchone()
                if res:
                    response = "ok"
                    print("ok")
                    client_socket.sendto(response.encode('UTF-8'), client_address)
                    conn.commit()
                else:
                    print(res)
                    response = f"auth failed"
                    client_socket.sendto(response.encode('UTF-8'), client_address)

            elif data.decode().startswith("/set"):
                com, v, da, n = data.decode('UTF-8').split("-=S=-")
                conn, cursor = get_c_c()
                cursor.execute(f"UPDATE users SET {v} = ? WHERE nick = ?", (da, n))
                conn.commit()
                response = "ok"
                client_socket.sendto(response.encode('UTF-8'), client_address)

            elif data.decode().startswith("/add_acc"):
                conn, cursor = get_c_c()
                com, n1, p1, ip1, pc = data.decode('UTF-8').split("-=S=-")
                cursor.execute("INSERT INTO users (nick, password, IP, pc) VALUES (?, ?, ?, ?)", (n1, p1, ip1, pc))
                conn.commit()
                response = f"ok"
                client_socket.sendto(response.encode('UTF-8'), client_address)

            elif data.decode().startswith("/get_settings"):
                com, n = data.decode('UTF-8').split("-=S=-")
                conn, cursor = get_c_c()
                cursor.execute("SELECT desc FROM users WHERE nick = ?", (n,))
                res1 = cursor.fetchone()
                if res1:    
                    response = f"/get_settings-=S=-{n}-=S=-{res1[0]}"
                    print(response)
                    client_socket.sendto(response.encode('UTF-8'), client_address)
                    conn.commit()

            elif data.decode().startswith("/text"):
                print("/text")
                com, n, m = data.decode('UTF-8').split("-=S=-")
                conn, cursor = get_c_c()
                response = f"/text-=S=-{n}: {m}"
                with open("msgs.txt", "a") as fi:
                    fi.write(f"{n}: {m}\n")
                for a in clients:
                    client_socket.sendto(response.encode('UTF-8'), a)
                print(client_address)
            
            elif data.decode().startswith("/getmsgs"):
                print("/getmsgs")
                com, n = data.decode('UTF-8').split(":")
                with open("msgs.txt", "r") as fi:
                    d = [line.strip() for line in fi]

                for a in clients:
                    client_socket.sendall(json.dumps(d).encode('UTF-8'), client_address)
                    

            else:
                pass
            # Отправляем ответ клиенту

    finally:
        # Очищаем соединение
        client_socket.close()
        print("F")

if __name__ == "__main__":
    # Создаем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = socket.gethostbyname(socket.gethostname())
    # Привязываем сокет к адресу и порту
    server_address = (str(host_ip), 10000) #64258
    server_socket.bind(server_address)
    print("==============\n=" + host_ip + "=\n==============")
    # Начинаем прослушивать входящие подключения
    server_socket.listen(10)

    print('Сервер запущен, ожидаю подключений...')

    while True:
        # Ожидаем подключение клиента
        print('Ожидаю подключение...')
        client_socket, client_address = server_socket.accept()
        clients.append(client_address)

        # Создаем новый поток для обработки клиента
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

