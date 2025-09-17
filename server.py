import socket
import threading
import psutil
import time
import sys
from datetime import datetime

monitores_ativos = {}   #chave uma tupla(client_socket, monitor_id) -> {"tipo": "CPU"/"Memória", "ativo": True, "thread": thread, "intervalo": intervalo}. Um dicionário para armazenar os monitores ativos, sendo os dados desses monitores guardados em dicionarios também só que internos 
lock = threading.Lock() #para garantir acesso exclusivo aos monitores ativos ao dicionário compartilhado entre as threads
clientes_ativos = 0
lock_clientes = threading.Lock()  #para garantir acesso exclusivo ao contador de clientes ativos
max_clientes = int(sys.argv[1])  #número máximo de clientes simultâneos

def monitor_cpu(client_socket, intervalo, monitor_id):
    #primeira leitura descartada para não mostrar uso 0%
    psutil.cpu_percent(interval=None)  # descarta a primeira leitura
    time.sleep(intervalo)  # espera o intervalo antes de começar a enviar dados
    while True:
        with lock:
            if not monitores_ativos.get((client_socket, monitor_id), {}).get("ativo", False):
                break
        uso_cpu = psutil.cpu_percent(interval=None)
        client_socket.sendall(f"[ID {monitor_id}] [{datetime.now().strftime('%H:%M:%S')}] CPU: {uso_cpu}%\n".encode())
        time.sleep(intervalo)

def monitor_memoria(client_socket, intervalo, monitor_id):
    #primeira leitura descartada para ficar coerente com o monitoramento de CPU
    psutil.virtual_memory().percent  # descarta a primeira leitura
    time.sleep(intervalo)  # espera o intervalo antes de começar a enviar dados
    while True:
        with lock:
            if not monitores_ativos.get((client_socket, monitor_id), {}).get("ativo", False):
                break
        mem = psutil.virtual_memory().percent #porcentagem de uso da memória
        client_socket.sendall(f"[ID {monitor_id}] [{datetime.now().strftime('%H:%M:%S')}] Memória: {mem}%\n".encode())
        time.sleep(intervalo)

def handle_client(client_socket, addr):
    global clientes_ativos  #variável global para contar clientes ativos
    monitor_id = 0  #É o id de cada monitor para cada cliente.
    threads_monitor = []    #lista para armazenar as threads de monitoramento ativas para esse cliente
    with lock_clientes:
        clientes_ativos += 1
        if clientes_ativos > max_clientes:
            client_socket.sendall("Máximo de clientes atingido. Tente novamente mais tarde.\n".encode())
            client_socket.close()
            clientes_ativos -= 1
            return #garante que não vai continuar tentando enviar
    #mandando mensagem ao conectar
    client_socket.sendall(f"{datetime.now().strftime('%H:%M:%S')}: CONECTADO!!\n".encode()) #sendall garante que toda a mensagem seja enviada e nao só parte dela como pode ocorrer com o send
    client_socket.sendall( "Comandos disponíveis:\n"
        "cpu-<segundos>  → Inicia monitor de CPU\n"
        "mem-<segundos>  → Inicia monitor de Memória\n"
        "list  → Lista monitores ativos\n"
        "quit-<ID>  → Encerra monitor pelo ID\n"
        "exit  → Encerra todos os monitores ativos e sai\n".encode())
    try:
        while True:
            request = client_socket.recv(1024).decode().strip() #para ler até 1024 bytes, decode transforma os bytes recebidos em string e encode transforma a string em bytes, o padrao é utf-8. Strip remove espaços em branco no começo e no final da string
            if not request: 
                break
            #comando para monitor CPU
            if request.lower().startswith("cpu-"):   #se o comando começa com cpu-
                partes = request.split("-") #divide no - em uma lista de dois elementos
                if len(partes) == 2 and partes[1].isdigit():
                    intervalo = int(partes[1])  #pega o segundo elemento que é o intervalo em segundos
                    monitor_id += 1
                    thread = threading.Thread(target=monitor_cpu, args=(client_socket, intervalo, monitor_id))  #cria uma thread para monitorar a CPU, args é uma tupla com os argumentos que serão passados para a função monitor_cpu
                    with lock:
                        monitores_ativos[(client_socket, monitor_id)] = {"tipo": "CPU", "ativo": True, "thread": thread, "intervalo":intervalo}    #adiciona o monitor ativo no dicionario de monitores ativos, está no lock porque é um dicionario compartilhado entre as threads
                    thread.start()
                    threads_monitor.append(thread)  #adiciona a thread na lista de threads de monitoramento ativas
                    client_socket.sendall(f"Monitor CPU iniciado com ID {monitor_id}.\n".encode())
                else:
                    client_socket.sendall("Comando inválido. Use cpu-<segundos>\n".encode())
            #comando para monitor Memória
            elif request.lower().startswith("mem-"): #se o comando começa com mem-
                partes = request.split("-") #divide no - em uma lista de dois elementos
                if len(partes) == 2 and partes[1].isdigit():
                    intervalo = int(partes[1])  #pega o segundo elemento que é o intervalo em segundos
                    monitor_id += 1
                    thread = threading.Thread(target=monitor_memoria, args=(client_socket, intervalo, monitor_id))  #cria uma thread para monitorar a Memória, args é uma tupla com os argumentos que serão passados para a função monitor_memoria
                    with lock:
                        monitores_ativos[(client_socket, monitor_id)] = {"tipo": "Memória", "ativo": True, "thread": thread, "intervalo":intervalo}    #adiciona o monitor ativo no dicionario de monitores ativos, está no lock porque é um dicionario compartilhado entre as threads
                    thread.start()
                    threads_monitor.append(thread)  #adiciona a thread na lista de threads de monitoramento ativas
                    client_socket.sendall(f"Monitor Memória iniciado com ID {monitor_id}.\n".encode())
                else:
                    client_socket.sendall("Comando inválido. Use mem-<segundos>\n".encode())
            #comando para listar monitores ativos
            elif request.lower() == "list":
                lista = ""
                for (cs, mid), info in monitores_ativos.items():
                    if cs == client_socket and info["ativo"]:
                        lista += f"ID {mid}: tipo={info['tipo']} intervalo={info['intervalo']}\n"  
                    if lista == "":
                        lista = "Nenhum monitor ativo.\n"
                client_socket.sendall(f"Monitores ativos:\n{lista}\n".encode())
            #comando para encerrar monitor específico
            elif request.lower().startswith("quit-"):    #se o comando começa com quit-
                partes = request.split("-") #divide no - em uma lista de dois elementos
                if len(partes) == 2 and partes[1].isdigit():
                    mid = int(partes[1])    #pega o segundo elemento que é o id do monitor (mid)
                    key = (client_socket, mid)
                    if key in monitores_ativos:
                        monitores_ativos[key]["ativo"] = False  #faz o loop do monitor parar
                        monitores_ativos[key]["thread"].join()  #espera a thread terminar
                        client_socket.sendall(f"Monitor {mid} finalizado.\n".encode())
                    else:
                        client_socket.sendall(f"Monitor {mid} não encontrado.\n".encode())
                else:
                    client_socket.sendall("Comando inválido. Use quit-<ID>\n".encode())
            #comando para encerrar todos os monitores e sair
            elif request.lower() == "exit":
                client_socket.sendall("Encerrando todos os monitores...\n".encode())
                with lock:
                    for (cs, mid), info in monitores_ativos.items():
                        if cs == client_socket:
                            info["ativo"] = False
                for t in threads_monitor:
                    t.join()    #espera as threads terminarem
                break
            #comando inválido
            else:
                client_socket.sendall("Comando inválido.\n".encode())
    #se der erro ou chegar no break usando exit, fecha a conexão
    finally:
        with lock:
            for (cs, mid), info in monitores_ativos.items():
                if cs == client_socket:
                    info["ativo"] = False
        for t in threads_monitor:
            t.join()    #espera as threads terminarem
        client_socket.close()   #fecha o socket do cliente
        with lock_clientes: #acessa o contador de clientes ativos
            clientes_ativos -= 1
        print(f"Conexão encerrada: {addr}")

def start_server():
    global clientes_ativos #variável global para contar clientes ativos
    server_ip="127.0.0.1"   #servidor localhost
    port=8000   #porta do servidor
    #criar o sobjeto socket
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #primeiro argumento especifica que estamos usando ip do tipo ipv4 e o segundo que estamos usando o protocolo tcp
        server.bind((server_ip, port))  #vincula o servidor ao ip e porta especificos
        #ouvir conexoes recebidas
        server.listen()    #número máximo de conexões pendentes, esperando para serem aceitas pelo server.accept() 
        print(f"Escutando em:\nIP servidor:{server_ip}\nPorta Servidor:{port}")
        while True:
            #aceitar conexao do cliente
            client_socket, addr = server.accept()   #client socket: cria um novo objeto socket para esse cliente especifico. Addr: o endereco do cliente que se conectou em uma tupla (ip, porta), ip e porta do cliente
            #criar uma thread para lidar com o cliente
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.start()
    except:
        print(f"Erro ao iniciar o servidor")
    finally:
        server.close()

start_server()