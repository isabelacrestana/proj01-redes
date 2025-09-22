# Cliente-Servidor para Monitoramento de Recursos

Este projeto implementa um **servidor TCP multi-threaded** e um **cliente** que se comunicam via sockets.  
O servidor permite que clientes solicitem monitoramento em tempo real de **uso de CPU** e **memória RAM**, com intervalos configuráveis.

---

## 📂 Estrutura do Projeto

- `server.py` → Servidor que aceita múltiplos clientes e gerencia monitores de CPU e memória.
- `cliente.py` → Cliente que se conecta ao servidor e envia comandos.

---

## ⚙️ Requisitos

- Python 3.8+
- Bibliotecas necessárias:
  `psutil`

- Instalação do `psutil`:
```bash
pip install psutil
```
## ▶️ Como Executar
<b>1. Inicie o servidor</b><br>
O servidor recebe como argumento o número máximo de clientes simultâneos:

```bash
python server.py 3
```
- Esse exemplo limita a 3 clientes conectados ao mesmo tempo.

O servidor roda em:

IP: 127.0.0.1
Porta: 8000

<b>2. Conecte um cliente</b><br>
Em outro terminal:

```bash
python cliente.py
```
Se conectarão múltiplos clientes, basta abrir mais terminais e rodar o comando acima.

## ⌨️ Comandos disponíveis no cliente
Após conectar, digite no terminal do cliente:

| Comando           | Descrição                                         | Exemplo          |
|------------------|--------------------------------------------------|----------------|
| cpu-<segundos>    | Inicia monitor de CPU no intervalo informado    | cpu-2           |
| mem-<segundos>    | Inicia monitor de Memória no intervalo informado| mem-5           |
| list              | Lista todos os monitores ativos do cliente      | list            |
| quit-<ID>         | Encerra um monitor específico pelo ID          | quit-1          |
| exit              | Encerra todos os monitores ativos e desconecta o cliente | exit |

## 📖 Exemplo de Uso
### No terminal do cliente:<br><br>
**EXEMPLO 1: Monitoramento de CPU**<br><br>
**Entrada:**
```bash
> cpu-3
```

**Saída recebida no cliente:**<br>
```
Monitor CPU iniciado com ID 1.
```

**Saída recebida no servidor:**<br>
```
[ID 1] [12:00:01] CPU: 14%
[ID 1] [12:00:04] CPU: 22%
```

---

**EXEMPLO 2: Monitoramento de Memória**<br><br>
**Entrada:**
```bash
> mem-5
```
**Saída recebida no cliente:**<br>
```
Monitor Memória iniciado com ID 2.
```

**Saída recebida do servidor:**<br>
```
[ID 2] [12:00:06] Memória: 45%<br>
```

---

**EXEMPLO 3: Listando monitores ativos:**<br><br>
**Entrada:**
```bash
> list
```

**Saída recebida no cliente:**<br>
```
Monitores ativos:
ID 1: tipo=CPU intervalo=3
ID 2: tipo=Memória intervalo=5
```
---

**EXEMPLO 4: Encerrando um monitor específico**<br><br>
**Entrada:**
```bash
> quit-1
```
**Saída recebida no cliente:**<br>
```
Monitor 1 finalizado.
```
---

**EXEMPLO 5: Desconectando o cliente**<br>
```bash
> exit
```
**Saída recebida no cliente:**<br>
```
Cliente encerrado.
```