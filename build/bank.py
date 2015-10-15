import socket
import os
import sys
import signal
from decimal import *

try: 
    commonAlreadyHere
except NameError:
    from common import *
from Crypto.PublicKey import RSA

class Bank:

	def __init__(self):
		self.port = 3000
		self.authFileName = 'bank.auth'
		self.checkArguments()

		self.secretKey = ''
		self.atmPublicKey = ''
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
			# bank public key
			self.secretKey = RSA.generate(2048)
			publicKey = self.secretKey.publickey()
			authFile.write(publicKey.exportKey('PEM'))

			# keys separator
			authFile.write('@@@@@')

			# privateKey for ATM
			atmPrivateKey = RSA.generate(2048)
			authFile.write(atmPrivateKey.exportKey('PEM'))
			self.atmPublicKey = atmPrivateKey.publickey()

			# keys separator
			authFile.write('@@@@@')

			# AES encryption key
			alphabet = string.printable.replace('@','')
			self.AESKey = ''.join([rand.choice(alphabet) for byte in range(32)])
			authFile.write(self.AESKey)

		print 'created'
		sys.stdout.flush()

	def exit_clean(self, signum, frame):
		self.s.shutdown(socket.SHUT_RDWR)
		self.s.close()
		raise ret0

	def listen2network(self):
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind(('127.0.0.1', self.port))
		self.s.listen(1)

		while 1:
			self.fieldsDict = dict()

			c = self.s.accept()
			self.cli_conn, cli_addr = c

			try:
				self.treatMessage(receiveMessage(self.cli_conn, sEncryptionKey=self.AESKey, sSignatureKey=self.atmPublicKey))

			except ret255:
				sys.stdout.flush()
			except ret63:
				print 'protocol_error'
				sys.stdout.flush()
			except Exception, e:
				debug('Exception' + str(e))
			finally:
				self.cli_conn.shutdown(socket.SHUT_RDWR)
				self.cli_conn.close()

			
	def sendReply(self, bankAnswer, bankMessage = ''):
		replyText=('atmID=' + self.fieldsDict['atmID'] + ' bankAns='+{True:'y', False:'n'}[bankAnswer]+ bankMessage)

		sendMessage(self.cli_conn, replyText, sEncryptionKey=self.AESKey, sSignatureKey=self.secretKey)
		self.knownAtms[self.fieldsDict['atmID']]['outgoing']=str(1+int(self.knownAtms[self.fieldsDict['atmID']]['outgoing']))
		
	def treatNewAccount(self):
		if (self.fieldsDict['account'] in self.accountHolders
		or  self.fieldsDict['$'] < Decimal('10.00')):
			self.sendReply(False)
		else:
			accountDetails = dict()
			accountDetails['timestamp'] = float(self.fieldsDict['timestamp'])
			accountDetails['pin'] = str(rand.randint(0, 1e12))
			accountDetails['$'] = Decimal(self.fieldsDict['$'])

			self.accountHolders[self.fieldsDict['account']] = accountDetails

			message = ' pin=' + str(accountDetails['pin']) + ' timestamp=' + self.fieldsDict['timestamp']

			self.sendReply(True, message)
			print('{"account":"'+self.fieldsDict['account']+'","initial_balance":%.2f}') % accountDetails['$']
			sys.stdout.flush()

	def treatDeposit(self):
		if self.validateIncomingOperation():
			depositAmount = Decimal(self.fieldsDict['$'])

			if depositAmount <= Decimal('0.00'):
				self.sendReply(False)
			else:
				self.accountHolders[self.fieldsDict['account']]['$'] += depositAmount

			message = ' timestamp=' + self.fieldsDict['timestamp']

			self.sendReply(True, message)
			print('{"account":"' + self.fieldsDict['account'] + '","deposit":%.2f}') % depositAmount
			sys.stdout.flush()

	def treatWithdrawal(self):
		if self.validateIncomingOperation():
			currentBalance = self.accountHolders[self.fieldsDict['account']]['$']
			withdrawAmount = Decimal(self.fieldsDict['$'])

			if  (self.fieldsDict['$'] <= Decimal('0.00')
				or  currentBalance < withdrawAmount):
				self.sendReply(False)
			else:
				self.accountHolders[self.fieldsDict['account']]['$'] = currentBalance - withdrawAmount

				message = ' timestamp=' + self.fieldsDict['timestamp']

				self.sendReply(True, message)

				print('{"account":"' + self.fieldsDict['account'] + '","withdraw":%.2f}') % withdrawAmount
				sys.stdout.flush()

	def treatGetBalance(self):
		if self.validateIncomingOperation():
			message = ' $=' + str(self.accountHolders[self.fieldsDict['account']]['$']) + ' timestamp=' + self.fieldsDict['timestamp']

			self.sendReply(True, message)

			print('{"account":"'+self.fieldsDict['account']+'","balance":%.2f}') % self.accountHolders[self.fieldsDict['account']]['$']
			sys.stdout.flush()
	
	def treatMessage(self, message):
		self.fieldsDict = message
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
except ret255, e:
	debug('ret255: ' + str(e))
	sys.exit(-1)
except ret0:
	sys.exit(0)
except Exception, e:
	debug('Exception: ' + str(e))
	sys.exit(-1)
