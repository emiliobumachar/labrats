import socket
from common import *


balance=10.00
atmID=str(rand.randint(0,1e12))

#TODO get operation from input
print("    RatLABS ATM    ")
print("""
g)        Balance
w)        Withdraw
d)        Deposit
q)        Quit
n)	  New Account


""")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 3000)) #TODO read ip and port
Option=99
while Option!='q':
        Option=raw_input("Enter Option: ")

        if Option=='g':
                print("Balance   ",balance)
                sendPlainText(s, 'atmID='+atmID+' action=g atmAns=y account=SomeGuy')

        if Option=='w':
                print("Balance    ",balance)
                Withdraw=float(input("Enter Withdraw amount  "))
                if Withdraw>0:
                        forewardbalance=(balance-Withdraw)
                        print("Foreward Balance   ",forewardbalance)
                        sendPlainText(s, 'atmID='+atmID+' action=w atmAns=y $='+str(Withdraw)+' account=SomeGuy')
                elif Withdraw>balance:
                        print("No funs in account")
                else:
                        print("None withdraw made")

        if Option=='d':
                print("Balance   ",balance)
                Deposit=float(input("Enter deposit amount  "))
                if Deposit>0:
                        forewardbalance=(balance+Deposit)
                        print("Forewardbalance   ",forewardbalance)
                        sendPlainText(s, 'atmID='+atmID+' action=d atmAns=y $='+str(Deposit)+' account=SomeGuy')
                else:
                        print("None deposit made")
                        sendPlainText(s, 'atmID='+atmID+' action=d atmAns=n $='+str(Deposit)+' account=SomeGuy')
        if Option=='n':
                sendPlainText(s, 'atmID='+atmID+' action=n atmAns=y $='+str(balance)+' account=SomeGuy')


s.close()
exit()
	

