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

		debug('Bank server running on port:' + str(self.port))
		debug('AuthFile name:' + self.authFileName)

	def createAuthFile(self):
		if os.path.isfile(self.authFileName):
			debug('Auth file already exists')
			raise ret255
		with open (self.authFileName,'w') as authFile:
			authFile.write(str(self.secretKey))

		print 'created'
		sys.stdout.flush()

	def exit_clean(self, signum, frame):
		sys.exit(0)

	def listen2network(self):
		self.s.bind(('127.0.0.1', 3000))
		self.s.listen(1)

		while 1:
			c = self.s.accept()
			self.cli_conn, cli_addr = c

			try:
				data = self.cli_conn.recv(1024) # check buffer limit
				#debug( 'data:' + data)

				self.treatMessage(data)

			except Exception, e:
				print 'protocol_error'
				debug(e)
				sys.stdout.flush()

			finally:
				self.cli_conn.close()

			
	def sendReply(self, bankAnswer, bankMessage = ''):
		replyText=('atmID=' + self.fieldsDict['atmID'] + ' bankAns='+{True:'y', False:'n'}[bankAnswer]+ bankMessage)

		sendPlainText(self.cli_conn, replyText)
		self.knownAtms[self.fieldsDict['atmID']]['outgoing']=str(1+int(self.knownAtms[self.fieldsDict['atmID']]['outgoing']))
		
	def treatNewAccount(self):
		if (self.fieldsDict['account'] in self.accountHolders
		or  self.fieldsDict['$']<10.00):
			self.sendReply(False)
		else:
			accountDetails = dict()
			accountDetails['timestamp'] = float(self.fieldsDict['timestamp'])
			accountDetails['pin'] = str(rand.randint(0, 1e12))
			accountDetails['$'] = float(self.fieldsDict['$'])

			self.accountHolders[self.fieldsDict['account']] = accountDetails

			message = ' pin=' + str(accountDetails['pin']) + ' timestamp=' + self.fieldsDict['timestamp']

			self.sendReply(True, message)
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
		if self.validateIncomingOperation():
			currentBalance = self.accountHolders[self.fieldsDict['account']]['$']
			withdrawAmount = float(self.fieldsDict['$'])

			if  (self.fieldsDict['$'] <= 0.00
				or  currentBalance < withdrawAmount):
				self.sendReply(False)
			else:
				self.accountHolders[self.fieldsDict['account']]['$'] = currentBalance - withdrawAmount

				message = ' timestamp=' + self.fieldsDict['timestamp']

				self.sendReply(True, message)

				print('{"account":"' + self.fieldsDict['account'] + '","withdraw":' + self.fieldsDict['$'] + '}')
				sys.stdout.flush()

	def treatGetBalance(self):
		if self.validateIncomingOperation():
			message = ' $=' + str(self.accountHolders[self.fieldsDict['account']]['$']) + ' timestamp=' + self.fieldsDict['timestamp']

			self.sendReply(True, message)

			print('{"account":"'+self.fieldsDict['account']+'","balance":'+str(self.accountHolders[self.fieldsDict['account']]['$'])+'}')
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

	def validateIncomingOperation(self):
		if self.fieldsDict['account'] not in self.accountHolders:
			debug('account doesnt exist')
			self.sendReply(False)
			return False

		elif self.accountHolders[self.fieldsDict['account']]['pin'] != self.fieldsDict['pin']:
			debug('server pin: ' + self.accountHolders[self.fieldsDict['account']]['pin'])
			debug('atm pin: ' + self.fieldsDict['pin'])
			debug('invalid pin')
			self.sendReply(False)
			return False

		elif self.accountHolders[self.fieldsDict['account']]['timestamp'] >= float(self.fieldsDict['timestamp']):
			debug('sever timestamp: ' + self.accountHolders[self.fieldsDict['account']]['timestamp'])
			debug('atm timestamp: ' + str(self.fieldsDict['timestamp']))
			debug('invalid timestamp')
			self.sendReply(False)
			return False

		else:
			# update timestamp
			self.accountHolders[self.fieldsDict['account']]['timestamp'] = float(self.fieldsDict['timestamp'])
			return True


try:
	bankObject=Bank()	
except ret255:
	sys.exit(-1)
except Exception, e:
	debug('unexpected error:' + str(e))
	sys.exit(-1)
