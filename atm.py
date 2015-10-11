import socket
import sys
from common import *

print("    RatLABS ATM    ")

class Atm:
    def __init__(self):
        self.atmID = str(rand.randint(0,1e12))
        self.port = 3000
        self.authFileName = 'bank.auth'
        self.ipAddress = '127.0.0.1'
        self.cardFileName = ''
        self.account = ''
        self.operation = ''
        self.amount = 0.0
        self.checkArguments()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ipAddress, self.port))
        self.treatOperation()

    def checkArguments(self):
        print sys.argv
        #['./bank.py', '-p', '1024', '-s', 'auth.file']

        argc = len(sys.argv)

        if argc > 13:
            raise ret255

        index = 0
        portSpecified = False
        authFileSpecified = False
        ipSpecified = False
        cardFileSpecified = False
        accountSpecified = False

        while index < argc:

            if index == 0:
                index += 1
                continue

            # port
            elif (sys.argv[index] == '-p') and (portSpecified == False):
                index += 1
                portSpecified = True
                validateNumbers(sys.argv[index])
                self.port = int(sys.argv[index])

            elif (sys.argv[index][0:2] == '-p') and (portSpecified == False):
                portSpecified = True
                portString = sys.argv[index][2:]
                validateNumbers(portString)
                self.port = int(portString)

            # auth file name
            elif (sys.argv[index] == '-s') and (authFileSpecified == False):
                index += 1
                authFileSpecified = True
                self.authFileName = str(sys.argv[index])

            elif (sys.argv[index][0:2] == '-s') and (authFileSpecified == False):
                authFileSpecified = True
                self.authFileName = str(sys.argv[index][2:])

            # server ip
            elif (sys.argv[index] == '-i') and (ipSpecified == False):
                index += 1
                ipSpecified = True
                self.ipAddress = str(sys.argv[index])

            elif (sys.argv[index][0:2] == '-i') and (ipSpecified == False):
                ipSpecified = True
                self.ipAddress = str(sys.argv[index][2:])

            # card file
            elif (sys.argv[index] == '-c') and (cardFileSpecified == False):
                index += 1
                cardFileSpecified = True
                self.cardFileName = str(sys.argv[index])

            elif (sys.argv[index][0:2] == '-c') and (cardFileSpecified == False):
                cardFileSpecified = True
                self.cardFileName = str(sys.argv[index][2:])

            # account
            elif (sys.argv[index] == '-a') and (accountSpecified == False):
                index += 1
                accountSpecified = True
                self.account = str(sys.argv[index])

            elif (sys.argv[index][0:2] == '-a') and (accountSpecified == False):
                accountSpecified = True
                self.account = str(sys.argv[index][2:])

            # new account, deposit and withdraw operations
            elif (((sys.argv[index] == '-n')
                or (sys.argv[index] == '-d')
                or (sys.argv[index] == '-w'))
                and (self.operation == '')):
                index += 1
                self.operation = sys.argv[index][1]
                self.amount = str(sys.argv[index])

            elif (((sys.argv[index][0:2] == '-n')
                or (sys.argv[index][0:2] == '-n')
                or (sys.argv[index][0:2] == '-n'))
                and (self.operation == '')):
                self.operation = sys.argv[index][1]
                self.amount = str(sys.argv[index][2:])

            # deposit operation
            elif (sys.argv[index] == '-g') and (self.operation == ''):
                index += 1
                self.operation = 'g'

            else:
                print 'raise args'
                raise ret255

            index += 1

        if not accountSpecified:
            raise ret255

        validatePortNumber(self.port)
        validateFileName(self.authFileName)

        print 'Atm contacting server on ip:', self.ipAddress
        print 'Atm contacting server on port:', self.port
        print 'AuthFile name:', self.authFileName
        print 'CardFile name:', self.cardFileName
        print 'Account:', self.account
        print 'Operation:', self.operation
        print 'Amount:', self.amount

    def treatOperation(self):
        if self.operation == 'g':
                #print("Balance   ",balance)
                sendPlainText(self.s, 'atmID='+self.atmID+' action=g atmAns=y account=SomeGuy')

        elif self.operation == 'w':
                #print("Balance    ",balance)
                Withdraw=float(input("Enter Withdraw amount  "))
                if Withdraw>0:
                        #forewardbalance=(balance-Withdraw)
                        #print("Foreward Balance   ",forewardbalance)
                        sendPlainText(self.s, 'atmID='+self.atmID+' action=w atmAns=y $='+str(Withdraw)+' account=SomeGuy')
                #elif Withdraw > balance:
                #        print("No funs in account")
                else:
                        print("None withdraw made")

        elif self.operation == 'd':
                #print("Balance   ",balance)
                Deposit=float(input("Enter deposit amount  "))
                if Deposit>0:
                        #forewardbalance=(balance+Deposit)
                        #print("Forewardbalance   ",forewardbalance)
                        sendPlainText(self.s, 'atmID='+self.atmID+' action=d atmAns=y $='+str(Deposit)+' account=SomeGuy')
                else:
                        print("None deposit made")
                        sendPlainText(self.s, 'atmID='+self.atmID+' action=d atmAns=n $='+str(Deposit)+' account=SomeGuy')

        elif self.operation == 'n':
                sendPlainText(self.s, 'atmID='+self.atmID+' action=n atmAns=y $='+str(balance)+' account=SomeGuy')

try:
    atmObject=Atm()
except ret255:
    sys.exit(-1)
except Exception, e:
    print 'unexpected error:', e
    sys.exit(-1)