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
            print('Получено:', data.decode())

            # Обрабатываем команду
            if data.decode().startswith('defgetcb'):
                response = 'okdefisd'
                client_socket.sendto(response.encode(), client_address)

            elif data.decode().startswith("/check"):
                com, ip = data.decode().split()
                conn, cursor = get_c_c()
                cursor.execute("SELECT IP FROM users WHERE IP=?", (ip,))
                res = cursor.fetchone()
                if res:
                    if ip == res[0]:
                        print(res)
                        response = f"auth {ip} ok"
                        print("ok")
                        client_socket.sendto(response.encode(), client_address)
                        conn.commit()
                    else:
                        print(res)
                        response = f"auth {ip} failed"
                        client_socket.sendto(response.encode(), client_address)
                else:
                    print("failed")
                    response = f"/check {ip} failed"
                    client_socket.sendto(response.encode(), client_address)
            elif data.decode().startswith("/set"):
                com, ip3, v, da = data.decode().split(":")
                conn, cursor = get_c_c()
                cursor.execute(f"UPDATE users SET {v} = ? WHERE IP = ?", (da, ip3,))
                conn.commit()
                response = "ok"
                client_socket.sendto(response.encode(), client_address)

            elif data.decode().startswith("/add_acc"):
                conn, cursor = get_c_c()
                com, n1, p1, ip1 = data.decode().split()
                cursor.execute("INSERT INTO users (nick, password, IP) VALUES (?, ?, ?)", (n1, p1, ip1))
                conn.commit()
                response = f"reg {ip1} ok"
                client_socket.sendto(response.encode(), client_address)

            elif data.decode().startswith("/get_settings"):
                com, ip2 = data.decode().split()
                conn, cursor = get_c_c()
                cursor.execute("SELECT nick, desc FROM users WHERE IP =?", (ip2,))
                res1 = cursor.fetchone()
                if res1:    
                    response = f"/get_settings:{res1[0]}:{res1[1]}"
                    client_socket.sendto(response.encode(), client_address)

            elif data.decode().startswith("/text"):
                print("/text")
                com, ip4, m = data.decode().split("-=S=-")
                conn, cursor = get_c_c()
                cursor.execute("SELECT nick FROM users WHERE IP =?", (ip4,))
                f = cursor.fetchone()[0]
                response = f"/text-=S=-{f}: {m}"
                with open("msgs.txt", "a") as fi:
                    fi.write(f"{f}:{m}\n")
                for a in clients:
                    client_socket.sendto(response.encode(), a)
                print(client_address)
            
            elif data.decode().startswith("/getmsgs"):
                print("/getmsgs")
                com, ip5 = data.decode().split(":")
                with open("msgs.txt", "r") as fi:
                    d = [line.strip() for line in fi]

                for a in clients:
                    client_socket.sendall(json.dumps(d).encode())
                    

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
