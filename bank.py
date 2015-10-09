import argparse
import socket
import os
from common import *


authFileName="bank.auth" #todo: get this name as a parameter

class Bank:

	def __init__(self):
		self.knownAtms={} #{atmID-as-string:{'incoming':latest-incoming-couter-as-string, 'outgoing':latest-outgoing-couter-as-string} for each atm that ever sent a message}
		secretKey=rand.randint(0,2**256-1)
		if os.path.isfile(authFileName):
			debug('File already exists')
			#raise ret255
		with open (authFileName,'w') as authFile:
			authFile.write(str(secretKey))
		self.actionList={'n':self.treatNewAccount,
				 'd':self.treatDeposit,
				 'w':self.treatWithdrawal,
				 'g':self.treatGetBalance}
		self.accountHolders={} #{account:balance for every account}
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listen2network()
		

	def listen2network(self):
		self.s.bind(('127.0.0.11', 3000))
		self.s.listen(1)

		while 1:
			self.c = self.s.accept()
			self.cli_conn, self.cli_addr = self.c

			data = self.cli_conn.recv(1024) # check buffer limit
			debug( 'data:'+data)

			#data = 'received: ' + data
			self.treatMessage(data)

			#self.cli_conn.send(data)
			self.cli_conn.close()
			
	def sendReply(self, bankAnswer):
		replyText=('atmID='+self.fieldsDict['atmID']+
				   #' msgCounter='+self.knownAtms[self.fieldsDict['atmID']]['outgoing']+
				   #' replyTo='+self.fieldsDict['msgCounter']+
				   ' bankAns='+{True:'y',False:'n'}[bankAnswer])
		if self.fieldsDict['action']=='g':
			replyText=replyText+' $='+str(self.accountHolders[self.fieldsDict['account']])
		sendPlainText(self.cli_conn, replyText)
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
		self.fieldsDict=msgParse(message)
		# delete this code if messageID is revoked, uncomment otherwise
		# if self.fieldsDict['atmID'] in self.knownAtms:#not first contact
			# if int(self.fieldsDict['msgCounter'])<=int(self.knownAtms[self.fieldsDict['atmID']]['incoming']): #replay attack or reorder attack!
				# return #ignore offending message
		#self.knownAtms[self.fieldsDict['atmID']]={'incoming':self.fieldsDict['msgCounter'],'outgoing':'0'}
		self.knownAtms[self.fieldsDict['atmID']]={'incoming':0,'outgoing':'0'}
		assert('action' in self.fieldsDict)
		assert self.fieldsDict['action'] in self.actionList
		self.actionList[self.fieldsDict['action']]()
		
try:
	bankObject=Bank()	
except ret255:
	print ('todo: return 255')
	#todo: return 255
