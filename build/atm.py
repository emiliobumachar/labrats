import socket
import sys
import os
import time
from decimal import *

try:
    commonAlreadyHere
except NameError:
    from common import *

debug("    RatLABS ATM    ")

class Atm:
    def __init__(self):
        self.atmID = str(rand.randint(0,1e12))
        self.port = 3000
        self.authFileName = 'bank.auth'
        self.ipAddress = '127.0.0.1'
        self.cardFileName = ''
        self.account = ''
        self.operation = ''
        self.amount = ''
        self.accountPin = ''
        self.timestamp = str(time.time())
        self.checkArguments()

        if self.operation != 'n':
            self.checkCardFile()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10.0)

        with open(self.authFileName, 'r') as authFile:
            keys = authFile.read().split('@@@@@')
            self.bankPublicKey = RSA.importKey(keys[0])
            self.secretKey = RSA.importKey(keys[1])
            self.AESKey = keys[2]

        self.treatOperation()

    def checkArguments(self):
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
                self.operation = sys.argv[index][1]
                index += 1
                self.amount = sys.argv[index]

            elif (((sys.argv[index][0:2] == '-n')
                or (sys.argv[index][0:2] == '-d')
                or (sys.argv[index][0:2] == '-w'))
                and (self.operation == '')):
                self.operation = sys.argv[index][1]
                self.amount = sys.argv[index][2:]

            # get balance operation
            elif (sys.argv[index] == '-g') and (self.operation == ''):
                self.operation = 'g'

            else:
                debug('raise args')
                raise ret255

            index += 1

        if not accountSpecified:
            raise ret255

        if not cardFileSpecified:
            self.cardFileName = str(self.account) + '.card'

        debug('validating port')
        validatePortNumber(self.port)
        debug('validating auth file name')
        validateFileName(self.authFileName)
        debug('validating card file name')
        validateFileName(self.cardFileName)
        debug('validating ip')
        validateIPAddress(self.ipAddress)
        debug('validating account name')
        validateAccountName(self.account)

        if len(self.amount) > 0:
            debug('validating amount')
            validateCurrencyNumbers(self.amount)
            self.amount = Decimal(self.amount)
            validateAmount(self.amount)

        debug('Atm contacting server on ip:' + self.ipAddress)
        debug('Atm contacting server on port:' + str(self.port))
        debug('AuthFile name:' + self.authFileName)
        debug('CardFile name:' + self.cardFileName)
        debug('Account:' + self.account)
        debug('Operation:' + self.operation)
        debug('Amount:' + str(self.amount))

    def treatOperation(self):
        if self.operation == 'g':
            reply = self.sendMessageToBank('atmID=' + self.atmID + ' action=g atmAns=y account=' + self.account + ' pin=' + self.accountPin + ' timestamp=' + self.timestamp)
            print('{"account":"' + self.account + '","balance":%.2f}') % Decimal(reply['$'])

        elif self.operation == 'w':
            if self.amount <= Decimal('0.00'):
                debug('Withdraw must be positive')
                raise ret255

            self.sendMessageToBank('atmID=' + self.atmID + ' action=w atmAns=y $=' + str(self.amount) + ' account=' + self.account + ' pin=' + self.accountPin + ' timestamp=' + self.timestamp)
            print('{"account":"' + self.account + '","withdraw":%.2f}') % self.amount

        elif self.operation == 'd':
            if self.amount <= Decimal('0.00'):
                debug('Deposit must be positive')
                raise ret255

            self.sendMessageToBank('atmID=' + self.atmID + ' action=d atmAns=y $=' + str(self.amount) + ' account=' + self.account + ' pin=' + self.accountPin + ' timestamp=' + self.timestamp)
            print('{"account":"' + self.account + '","deposit":%.2f}') % self.amount

        elif self.operation == 'n':
            if os.path.isfile(self.cardFileName):
                debug('Card file already exists')
                raise ret255

            elif self.amount < 10.00:
                debug('Initial balance less than the minimum allowed')
                raise ret255

            reply = self.sendMessageToBank('atmID='+self.atmID+' action=n atmAns=y $='+str(self.amount)+' account='+ self.account + ' timestamp=' + self.timestamp)

            with open (self.cardFileName, 'w') as cardFile:
                cardFile.write(reply['pin'])

            print('{"account":"'+self.account+'","initial_balance":%.2f}') % self.amount

        sys.stdout.flush()

    def checkCardFile(self):
        if not os.path.isfile(self.cardFileName):
            debug('Card file must exists')
            raise ret255

        with open (self.cardFileName, 'r') as cardFile:
            self.accountPin = cardFile.readline()

        if len(self.accountPin) <= 0:
            debug('Card file must contain the pin')
            raise ret255

        debug('pin:' + self.accountPin)

    def sendMessageToBank(self, message):
        self.s.connect((self.ipAddress, self.port))
        sendMessage(self.s, message, sEncryptionKey=self.AESKey, sSignatureKey=self.secretKey)
        reply = receiveMessage(self.s, sEncryptionKey=self.AESKey, sSignatureKey=self.bankPublicKey)
        validateBankAnswer(reply, self.atmID, self.timestamp)
        return reply

try:
    atmObject=Atm()
    raise ret0
except ret255:
    sys.exit(-1)
except ret63:
    sys.exit(63)
except ret0:
    sys.exit(0)
except:
    sys.exit(-1)