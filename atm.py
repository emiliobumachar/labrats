import socket

balance=10.00

#TODO get operation from input
print("    RatLABS ATM    ")
print("""
0)        TestTCP
1)        Balance
2)        Withdraw
3)        Deposit
4)        Quit


""")
Option=int(input("Enter Option: "))

if Option == 0:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 3000)) #TODO read ip and port
    s.send('tcp socket test')
    data = s.recv(1024) #TODO define limit
    s.close()
    print data

if Option==1:
    print("Balance   ",balance)


if Option==2:
    print("Balance    ",balance)
    Withdraw=float(input("Enter Withdraw amount  "))
    if Withdraw>0:
        forewardbalance=(balance-Withdraw)
        print("Foreward Balance   ",forewardbalance)
    elif Withdraw>balance:
        print("No funs in account")
    else:
        print("None withdraw made")

if Option==3:
    print("Balance   ",balance)
    Deposit=float(input("Enter deposit amount  "))
    if Deposit>0:
        forewardbalance=(balance+Deposit)
        print("Forewardbalance   ",forewardbalance)
    else:
        print("None deposit made")


if Option==4:
    exit()
