import socket
import threading

desconectado = False  # flag global para sinalizar que o servidor desconectou

def receber_msgs(cliente):
    #Thread separada para receber mensagens do servidor
    global desconectado
    try:
        while True:
            data = cliente.recv(1024) #recebe até 1024 bytes do servidor
            if not data:  # servidor fechou a conexão
                print("Servidor desconectou.")
                desconectado = True
                break
            print(data.decode(), end="") #imprime direto na tela, sem pular linha (end="" garante que não adiciona uma nova linha após a mensagem recebida)
    except:
        desconectado = True
    finally:
        cliente.close()

def cliente():
    global desconectado
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #cria o socket do cliente, primeiro argumento especifica que estamos usando ip do tipo ipv4 e o segundo que estamos usando o protocolo tcp
    server_ip = "127.0.0.1"  #ip do servidor
    port = 8000 #porta do servidor
    # conecta ao servidor
    cliente.connect((server_ip, port))
    print(f"Conectado ao servidor {server_ip}:{port}") #conecta o cliente ao servidor, passando o ip e a porta do servidor
    # Thread para receber mensagens do servidor
    threading.Thread(target=receber_msgs, args=(cliente,)).start() #precisa da virgula em args para ser uma tupla
    try:
        while not desconectado:
            msg = input("> ") #lê do teclado
            if not msg: #se a mensagem for vazia, não envia nada
                continue #evita enviar mensagens vazias, volta pro laço while not desconectado e espera nova entrada do usuário 
            try:
                cliente.sendall(msg.encode()[:1024])  #envia a mensagem para o servidor, codificando em bytes e limitando a 1024 bytes, para evitar problemas com mensagens muito longas (o [:1024] faz um slice dos bytes, pegando apenas os primeiros 1024 bytes)
            except:
                print("Não foi possível enviar: servidor desconectado.")
                break
            if msg.lower() == "exit":
                try:
                    cliente.sendall("exit".encode()) #envia o exit para o servidor
                except: #se der erro ao enviar, ignora
                    pass
                break
    except KeyboardInterrupt:
        print("Saindo do cliente...")
        cliente.sendall("exit".encode()) #envia o exit para o servidor
    finally:
        cliente.close()
        print("Cliente encerrado.")

cliente()