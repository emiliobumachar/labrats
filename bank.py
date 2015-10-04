import argparse
import socket
import parser
s = socket.socket(socket.PF_INET, socket.SOCK_STREAM)
s.listen()
global knownAtms={} #{atmID-as-string:latest-couter-as-string for each atm that ever sent a message}
global accountHolders={} #{account:balance for every account}
while 1:
    c = s.accept()
    cli_sock, cli_addr = c
	treatMessage(?)
	
treatNewAccount(fieldsDict):
	pass
treatDeposit(fieldsDict):
	pass
treatWithdrawal(fieldsDict):
	pass
treatGetBalance(fieldsDict):
	pass


actionList={'n':treatNewAccount,
			'd':treatDeposit,
			'w':treatWithdrawal,
			'g':treatGetBalance}
def treatMessage(message):
	fieldsDict=parser.parse(message)
	if fieldsDict['atmID'] in knownAtms:#not first contact
		if int(fieldsDict['msgCounter'])<=int(knownAtms[fieldsDict['atmID']]): #replay attack or reorder attack!
			return #ignore offending message
	knownAtms[fieldsDict['atmID']]=fieldsDict['msgCounter']
	assert('action' in fieldsDict)
	assert fieldsDict['action'] in actionList
	actionList[fieldsDict['action']](fieldsDict)
	