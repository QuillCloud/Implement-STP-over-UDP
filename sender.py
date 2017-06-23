from socket import *
from random import *
from collections import *
from time import *
from threading import *
from sys import *

def write_log(f, action, time, tp, pac):
    global t_start
    t = "{0:.3f}".format((time - t_start)*1000)
    b = pac.split('\n')
    h = b[0].split(' ')
    b.remove(b[0])
    b = '\n'.join(b)
    b = str(len(b))
    write = action+ (5 - len(action))*' ' + str(t) + (8 - len(t))*' ' + tp + (3 - len(tp))*' ' + str(h[0]) + \
            (11 - len(h[0]))*' ' + b + (5 - len(b))*' ' + h[1] + '\n'
    f.write(write)

def timeout_retransmit(wait_ack, pdrop, window, clientSocket, serverName, serverPort):
    global num_pac_drop
    global num_re
    num_re += 1
    re = window
    if PLD(pdrop):
        clientSocket.sendto(re[0].encode('utf-8'), (serverName, serverPort))
        write_log(f, "snd", time(), "D", re[0])
    else:
        num_pac_drop += 1
        write_log(f, "drop", time(), "D", re[0])
    global t
    t.cancel()
    t = Timer(timeinter, timeout_retransmit,(wait_ack, pdrop, window, clientSocket, serverName, serverPort))
    t.start()

def fast_retransmit(pdrop, f, n, window, wait_ack, MSS, clientSocket, serverName, serverPort):
    global num_re
    global num_pac_drop
    num_re += 1
    win = window
    wa = wait_ack
    seq = n + MSS
    for i in range(len(wa)):
        if seq == wa[i]:
            if PLD(pdrop):
                clientSocket.sendto(win[i].encode('utf-8'), (serverName, serverPort))
                write_log(f, "snd", time(), "D", win[i])
            else:
                num_pac_drop += 1
                write_log(f, "drop", time(), "D", win[i])

def PLD(pdrop):
    chance = randint(1, 100)
    chance = chance / 100
    if chance >= pdrop:
        return True
    if chance < pdrop:
        return False

def create_header(seqnumber, ack):
    cre_header = ['0', '0', '0', '0', '0']
    cre_header[0] = str(seqnumber)
    cre_header[1] = str(ack)
    return cre_header

def create_seg(f, size):
    packet = []
    file = open(f, 'r')
    line = file.read()
    count = 0
    while count < len(line):
        get = line[count:count + size]
        count += size
        packet.append(get)
    file.close()
    return packet, len(line)

def create_pac_and_exack(seg, isn, acknum):
    pac = []
    cur = isn
    ack = acknum
    ex_ack = []
    for i in range(len(seg)):
        h = create_header(cur, ack)
        cur = (cur + len(seg[i])) % 4294967295
        ex_ack.append(cur)
        sp = ' '.join(h) + '\n' + seg[i]
        pac.append(sp)
    return pac, ex_ack

def establish(header, clientSocket, serverName, serverPort, f):
    header[3] = str(1)
    isn = int(header[0])
    syn = ' '.join(header)
    write_log(f, "snd", time(), "S", syn)
    clientSocket.sendto(syn.encode('utf-8'), (serverName, serverPort))
    synack, serverAddress = clientSocket.recvfrom(2048)
    synack = synack.decode('utf-8')
    write_log(f, "rcv", time(), "SA", synack)
    header = synack.split(' ')
    if (header[2] == '1') and (header[3] == '1') and (int(header[1]) == (isn + 1) % 4294967295):
        header[3] = '0'
        header[2] = '1'
        header[0] = str((int(header[0]) + 1) % 4294967295)
        header[0], header[1] = header[1], header[0]
        syn = ' '.join(header)
        write_log(f, "snd", time(), "A", syn)
        clientSocket.sendto(syn.encode('utf-8'), (serverName, serverPort))
        return header
    return None

def finish(c,acknum, f):
    header = ['0', '0', '0', '0', '1']
    header[0] = str(c)
    header[1] = str(acknum)
    fin = ' '.join(header)
    write_log(f, "snd", time(), "F", fin)
    clientSocket.sendto(fin.encode('utf-8'), (serverName, serverPort))
    finack, serverAddress = clientSocket.recvfrom(2048)
    finack = finack.decode('utf-8')
    write_log(f, "rcv", time(), "A", finack)
    header = finack.split(' ')
    if header[2] == '1':
        serfin, serverAddress = clientSocket.recvfrom(2048)
        serfin = serfin.decode('utf-8')
        write_log(f, "rcv", time(), "F", serfin)
        ser_header = serfin.split(' ')
        if ser_header[4] == '1':
            last_header = ['0','0','1','0','0']
            last_header[1] = str((int(ser_header[0]) + 1) % 4294967295)
            last_header[0] = str(int(ser_header[1]))
            fin = ' '.join(last_header)
            write_log(f, "snd", time(), "A", fin)
            clientSocket.sendto(fin.encode('utf-8'), (serverName, serverPort))
            return True

num_pac_drop = 0
num_re = 0
num_dul_ack = 0
t_start = time()
serverName = argv[1]
serverPort = int(argv[2])
file = argv[3]
MWS = int(argv[4])
MSS = int(argv[5])
timeinter = int(argv[6]) / 1000
pdrop = float(argv[7])
sd = int(argv[8])
seed(sd)
clientSocket = socket(AF_INET, SOCK_DGRAM)
count = 0
win_size = MWS // MSS
window = deque(maxlen=win_size)                                         # create window
wait_ack = deque(maxlen=win_size)
s, amount_data = create_seg(file, MSS)                                  # create segments store in p
f = open('Sender_log.txt', 'w')
header = ['0', '0', '0', '0', '0']                                      # 0 seqnumber,1 acknumber,2 ack,3 syn,4 fin
client_isn = randint(1,4294967295)
seqnum = 0
n = 0
header[0] = str(client_isn)
dulpicate = 0
header = establish(header, clientSocket, serverName, serverPort, f)        # establish the TCP connection
if header is not None:
    seqnum = int(header[0]) % 4294967295
    acknum = header[1]
    p, ea = create_pac_and_exack(s, seqnum, acknum)
    for i in range(win_size):
        if PLD(pdrop):
            clientSocket.sendto(p[i].encode('utf-8'), (serverName, serverPort))
            write_log(f, "snd", time(), "D", p[i])
        else:
            num_pac_drop += 1
            write_log(f, "drop", time(), "D", p[i])
        window.append(p[i])
        wait_ack.append(ea[i])
    t = Timer(timeinter, timeout_retransmit,(wait_ack, pdrop, window, clientSocket, serverName, serverPort))
    t.start()
    while count < len(p):
        if t.finished.is_set() is True:
            if len(window) > 0:
                t.cancel()
                t = Timer(timeinter, timeout_retransmit,(wait_ack, pdrop, window, clientSocket, serverName, serverPort))
                t.start()
        ack, serverAddress = clientSocket.recvfrom(2048)
        ack = ack.decode('utf-8')
        get_header = ack.split(' ')
        if get_header[2] == '1':
            if int(get_header[1]) in wait_ack:
                for j in range(list(wait_ack).index(int(get_header[1])) + 1):
                    window.popleft()
                    wait_ack.popleft()
                    next_p = count + win_size
                    count += 1
                    if next_p < len(p):
                        if PLD(pdrop):
                            clientSocket.sendto(p[next_p].encode('utf-8'), (serverName, serverPort))
                            write_log(f, "snd", time(), "D", p[next_p])
                        else:
                            num_pac_drop += 1
                            write_log(f, "drop", time(), "D", p[next_p])
                        window.append(p[next_p])
                        wait_ack.append(ea[next_p])
                if len(window) > 0:
                    t.cancel()
                    t = Timer(timeinter, timeout_retransmit,(wait_ack, pdrop, window, clientSocket, serverName, serverPort))
                    t.start()
            else:
                num_dul_ack += 1
                if int(get_header[1]) == n:
                    dulpicate += 1
                    if dulpicate == 3:
                        fast_retransmit(pdrop, f, n, window, wait_ack, MSS, clientSocket,serverName,serverPort)
                        if len(window) > 0:
                            t.cancel()
                            t = Timer(timeinter, timeout_retransmit,(wait_ack, pdrop, window, clientSocket, serverName, serverPort))
                            t.start()
                else:
                    n = int(get_header[1])
                    dulpicate = 1


t.cancel()
close = finish(ea[-1], acknum, f)
if close is True:
    f.write("Amount of Data Transferred (in bytes)                    " + str(amount_data) + '\n')
    f.write("Number of Data Segments Sent (excluding retransmissions) " + str(len(s)) + '\n')
    f.write("Number of Packets Dropped (by the PLD module)            " + str(num_pac_drop) + '\n')
    f.write("Number of Retransmitted Segments                         " + str(num_re) + '\n')
    f.write("Number of Duplicate Acknowledgements received            " + str(num_dul_ack) + '\n')
    f.close()
    clientSocket.close()
