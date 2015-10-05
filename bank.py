import argparse
import socket
import parser
class bank:
	def __init__(self):
		self.knownAtms={} #{atmID-as-string:latest-couter-as-string for each atm that ever sent a message}
		self.accountHolders={} #{account:balance for every account}
		self.s = socket.socket(socket.PF_INET, socket.SOCK_STREAM)
		self.listen2network(self)
		self.actionList={'n':self.treatNewAccount,
						 'd':self.treatDeposit,
						 'w':self.treatWithdrawal,
						 'g':self.treatGetBalance}
	def listen2network(self):
		self.s.listen()
		while 1:
			c = s.accept()
			cli_sock, cli_addr = c
			treatMessage(self,cli_sock.?)
		
	def treatNewAccount(self):
		pass
	def treatDeposit(self):
		pass
	def treatWithdrawal(self):
		pass
	def treatGetBalance(self):
		pass


	
	def treatMessage(self, message):
		self.fieldsDict=parser.parse(message)
		if self.fieldsDict['atmID'] in self.knownAtms:#not first contact
			if int(self.fieldsDict['msgCounter'])<=int(self.knownAtms[self.fieldsDict['atmID']]): #replay attack or reorder attack!
				return #ignore offending message
		self.knownAtms[self.fieldsDict['atmID']]=self.fieldsDict['msgCounter']
		assert('action' in self.fieldsDict)
		assert self.fieldsDict['action'] in self.actionList
		self.actionList[self.fieldsDict['action']]()
	