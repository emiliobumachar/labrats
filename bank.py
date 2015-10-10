import socket
import os
import sys
import signal
from common import *

class Bank:

	def __init__(self):
		self.port = 3000
		self.authFileName = 'bank.auth'
		self.checkArguments()

		self.secretKey=rand.randint(0,2**256-1)
		self.createAuthFile()

		signal.signal(signal.SIGINT, self.exit_clean)
		signal.signal(signal.SIGTERM, self.exit_clean)

		self.knownAtms={} #{atmID-as-string:{'incoming':latest-incoming-couter-as-string, 'outgoing':latest-outgoing-couter-as-string} for each atm that ever sent a message}

		self.actionList={'n':self.treatNewAccount,
						 'd':self.treatDeposit,
						 'w':self.treatWithdrawal,
						 'g':self.treatGetBalance}
		self.accountHolders={} #{account:balance for every account}
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listen2network()
		
	def checkArguments(self):
		#print sys.argv
		#['./bank.py', '-p', '1024', '-s', 'auth.file']

		argc = len(sys.argv)

		if argc > 5:
			raise ret255

		index = 0
		portSpecified = False
		authFileSpecified = False

		while index < argc:

			if index == 0:
				index += 1
				continue

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

			elif (sys.argv[index] == '-s') and (authFileSpecified == False):
				index += 1
				authFileSpecified = True
				self.authFileName = str(sys.argv[index])

			elif (sys.argv[index][0:2] == '-s') and (authFileSpecified == False):
				authFileSpecified = True
				self.authFileName = str(sys.argv[index][2:])

			else:
				raise ret255

			index += 1

		validatePortNumber(self.port)
		validateFileName(self.authFileName)

		print 'Bank server running on port:', self.port
		print 'AuthFile name:', self.authFileName

	def createAuthFile(self):
		if os.path.isfile(self.authFileName):
			debug('File already exists')
			raise ret255
		with open (self.authFileName,'w') as authFile:
			authFile.write(str(self.secretKey))

		print 'created\n'
		sys.stdout.flush()

	def exit_clean(self, signum, frame):
		sys.exit(0)

	def listen2network(self):
		self.s.bind(('127.0.0.1', 3000))
		self.s.listen(1)

		while 1:
			c = self.s.accept()
			cli_conn, cli_addr = self.c

			try:
				data = cli_conn.recv(1024) # check buffer limit
				debug( 'data:'+data)

				#data = 'received: ' + data
				self.treatMessage(data)

				#self.cli_conn.send(data)

			except:
				print 'protocol_error\n'
				sys.stdout.flush()

			finally:
				cli_conn.close()

			
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
			sys.stdout.flush()

	def treatDeposit(self):
		if (self.fieldsDict['account'] not in self.accountHolders
		or  self.fieldsDict['$']<=0.00):
			self.sendReply(False)
		else:
			self.accountHolders[self.fieldsDict['account']]=self.accountHolders[self.fieldsDict['account']]+self.fieldsDict['$']
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","deposit":'+str(self.fieldsDict['$'])+'}')
			sys.stdout.flush()

	def treatWithdrawal(self):
		if (self.fieldsDict['account'] not in self.accountHolders
		or  self.fieldsDict['$']<=0.00
		or  self.accountHolders[self.fieldsDict['account']]<self.fieldsDict['$']):
			self.sendReply(False)
		else:
			self.accountHolders[self.fieldsDict['account']]=self.accountHolders[self.fieldsDict['account']]-self.fieldsDict['$']
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","withdraw":'+str(self.fieldsDict['$'])+'}')
			sys.stdout.flush()

	def treatGetBalance(self):
		if (self.fieldsDict['account'] not in self.accountHolders):
			self.sendReply(False)
		else:
			self.sendReply(True)
			print('{"account":"'+self.fieldsDict['account']+'","balance":'+str(self.accountHolders[self.fieldsDict['account']])+'}')
			sys.stdout.flush()
	
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
	sys.exit(-1)
