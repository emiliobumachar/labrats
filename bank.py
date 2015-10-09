import argparse
import socket
import parser
import string
import random
import os
rand=random.SystemRandom()
LENGTH_OF_ALL_PLAINTEXTS = 333
authFileName="bank.auth" #todo: get this name as a parameter

class ret255(Exception):
	pass
class Bank:

	def __init__(self):
		self.knownAtms={} #{atmID-as-string:{'incoming':latest-incoming-couter-as-string, 'outgoing':latest-outgoing-couter-as-string} for each atm that ever sent a message}
		secretKey=rand.randint(0,2**256-1)
		if os.path.isfile(authFileName):
			raise ret255
		with open (authFileName,'w') as authFile:
			authFile.write(str(secretKey))
		
		self.accountHolders={} #{account:balance for every account}
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listen2network()
		self.actionList={'n':self.treatNewAccount,
						 'd':self.treatDeposit,
						 'w':self.treatWithdrawal,
						 'g':self.treatGetBalance}

	def listen2network(self):
		self.s.bind(('127.0.0.1', 3000))
		self.s.listen(1)

		while 1:
			c = self.s.accept()
			cli_conn, cli_addr = c

			data = cli_conn.recv(1024) # check buffer limit
			print 'data:', data

			data = 'received: ' + data
			#treatMessage(self,cli_conn.?)

			cli_conn.send(data)
			cli_conn.close()
			
	def sendReply(self, bankAnswer):
		replyText=('atmID='+self.fieldsDict['atmID']+
				   ' msgCounter='+self.knownAtms[self.fieldsDict['atmID']]['outgoing']+
				   ' replyTo='+self.fieldsDict['msgCounter']+
				   ' bankAns='+{True:'y',False:'n'}[bankAnswer])
		if self.fieldsDict['action']=='g':
			replyText=replyText+' $='+str(self.accountHolders[self.fieldsDict['account']])
		replyText=replyText+' pad='
		replyText=replyText+rand.choice(string.ascii_letters)*(LENGTH_OF_ALL_PLAINTEXTS-len(replyText))
		#self.cli_sock.(replyText)
		self.knownAtms[self.fieldsDict['atmID']]['outgoing']=str(1+int(self.knownAtms[self.fieldsDict['atmID']]['outgoing']))
		
	def treatNewAccount(self):
		if (self.fieldsDict['account'] in self.accountHolders
		or  self.fieldsDict['$']<10.00):
			self.sendReply(False)
		else:
			self.accountHolders[self.fieldsDict['account']]=self.fieldsDict['$']
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","initial_balance":'+str(self.fieldsDict['$'])+'}')

	def treatDeposit(self):
		if (self.fieldsDict['account'] not in self.accountHolders
		or  self.fieldsDict['$']<=0.00):
			self.sendReply(False)
		else:
			self.accountHolders[self.fieldsDict['account']]=self.accountHolders[self.fieldsDict['account']]+self.fieldsDict['$']
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","deposit":'+str(self.fieldsDict['$'])+'}')

	def treatWithdrawal(self):
		if (self.fieldsDict['account'] not in self.accountHolders
		or  self.fieldsDict['$']<=0.00
		or  self.accountHolders[self.fieldsDict['account']]<self.fieldsDict['$']):
			self.sendReply(False)
		else:
			self.accountHolders[self.fieldsDict['account']]=self.accountHolders[self.fieldsDict['account']]-self.fieldsDict['$']
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","withdraw":'+str(self.fieldsDict['$'])+'}')

	def treatGetBalance(self):
		if (self.fieldsDict['account'] not in self.accountHolders):
			self.sendReply(False)
		else:
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","balance":'+str(self.accountHolders[self.fieldsDict['account']])+'}')
	
	def treatMessage(self, message):
		self.fieldsDict=parser.parse(message)
		if self.fieldsDict['atmID'] in self.knownAtms:#not first contact
			if int(self.fieldsDict['msgCounter'])<=int(self.knownAtms[self.fieldsDict['atmID']]['incoming']): #replay attack or reorder attack!
				return #ignore offending message
		self.knownAtms[self.fieldsDict['atmID']]={'incoming':self.fieldsDict['msgCounter'],'outgoing':'0'}
		assert('action' in self.fieldsDict)
		assert self.fieldsDict['action'] in self.actionList
		self.actionList[self.fieldsDict['action']]()
		
try:
	bankObject=Bank()	
except ret255:
	print ('todo: return 255')
	#todo: return 255
