from socket import *
from random import *
from sys import *
def create_ack(state):
    ack_header = ['0','0','1','0','0']
    ack_header[1] = str(state)
    ack = ' '.join(ack_header)
    ack = ack.encode("utf-8")
    return ack

seed(50)
already_ack = []
buffer = {}
state = 'listen'
serverPort = int(argv[1])
file = argv[2]
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
now_server = 0
while 1:
    message = ''
    message, clientAddress = serverSocket.recvfrom(2048)
    message = message.decode('utf-8')
    get = message.split('\n')
    header = get[0].split(' ')
    ack = ''
    content = ''
    #syn
    if header[3] == '1':
        state = 'syn'
        server_isn = randint(1,4294967295)
        now_server = server_isn
        header[1] = str((int(header[0]) + 1) % 4294967295)
        header[0] = str(server_isn)
        header[2] = '1'
        message = ' '.join(header)
        message = message.encode("utf-8")
        serverSocket.sendto(message, clientAddress)
        continue

    #ack of syn or fin
    if header[2] == '1':
        if header[1] == str((now_server + 2) % 4294967295):
            state = 'listen'
        elif header[1] == str((now_server + 1) % 4294967295):
            f = open(file, 'w')
            l = open('Receiver_log.txt', 'w')
            amount_data = 0
            num_seg = 0
            num_dul_seg = 0
            now_server = int(header[1])
            state = int(header[0]) % 4294967295
        continue

    #packets
    elif (header[2] == '0') and (header[3] == '0') and (header[4] == '0'):
        get.remove(get[0])
        if int(header[0]) == state:
            content = '\n'.join(get)
            f.write(content)
            amount_data += len(content)
            num_seg += 1
            state = (int(header[0]) + len(content)) % 4294967295
            already_ack.append(int(header[0]))
            while str(state) in buffer:
                content = '\n'.join(buffer[str(state)])
                f.write(content)
                amount_data += len(content)
                num_seg += 1
                buffer.pop(str(state))
                already_ack.append(state)
                state = (state + len(content)) % 4294967295
            ack = create_ack(state)
            serverSocket.sendto(ack, clientAddress)
            continue

        elif int(header[0]) not in already_ack:
            num_dul_seg += 1
            if (header[0]) not in buffer:
                buffer[header[0]] = get
            ack = create_ack(state)
            serverSocket.sendto(ack, clientAddress)
            continue

        else:
            num_dul_seg += 1
            continue

    #fin
    elif (header[4] == '1'):
        state = 0
        header[2] = '1'
        header[1] = header[0]
        header[0] = str(now_server)
        ack = ' '.join(header)
        ack = ack.encode("utf-8")
        serverSocket.sendto(ack, clientAddress)
        header[1] = str((int(header[1]) + 1) % 4294967295)
        header[0] = str((int(header[0]) + 1) % 4294967295)
        fin = ' '.join(header)
        fin = fin.encode("utf-8")
        serverSocket.sendto(fin, clientAddress)
        l.write("Amount of Data Received (in bytes)    " + str(amount_data) + '\n')
        l.write("Number of Data Segments Received      " + str(num_seg) + '\n')
        l.write("Number of duplicate segments received " + str(num_dul_seg) + '\n')
        l.close()
        f.close()
        already_ack = []
        buffer = {}
        now_server = 0
        continue






