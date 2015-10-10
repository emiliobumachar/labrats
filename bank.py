#!/usr/bin/python

import argparse
import socket
import parser
import string
import random
import sys
import re

rand=random.SystemRandom()
LENGTH_OF_ALL_PLAINTEXTS = 333

class Bank:

	def __init__(self):
		self.port = 3000
		self.authFile = 'bank.auth'
		self.checkArguments()
		#self.createAuthFile()
		self.knownAtms={} #{atmID-as-string:{'incoming':latest-incoming-couter-as-string, 'outgoing':latest-outgoing-couter-as-string} for each atm that ever sent a message}
		self.fieldsDict={}
		self.accountHolders={} #{account:balance for every account}
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listen2network()
		self.actionList={'n':self.treatNewAccount,
						 'd':self.treatDeposit,
						 'w':self.treatWithdrawal,
						 'g':self.treatGetBalance}

	def checkArguments(self):
		#print sys.argv
		#['./bank.py', '-p', '1024', '-s', 'auth.file']

		try:
			argc = len(sys.argv)

			if argc > 5:
				raise Exception

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
					self.port = int(sys.argv[index])

					#port number validation
					if self.port < 1024 or self.port > 65535:
						raise Exception

				elif (sys.argv[index] == '-s') and (authFileSpecified == False):
					index += 1
					authFileSpecified = True
					self.authFile = str(sys.argv[index])

					#authFile name validation
					if self.authFile == '.' or self.authFile == '..':
						raise Exception

					if not re.match('[_\-\.0-9a-z]{1,255}', self.authFile):
						raise Exception

				else:
					raise Exception

				index += 1

		except:
			sys.exit(-1)

		print 'Bank server running on port:', self.port
		print 'AuthFile name:', self.authFile

	def listen2network(self):
		self.s.bind(('127.0.0.1', self.port))
		self.s.listen(1)

		while 1:
			c = self.s.accept()
			cli_conn, cli_addr = c

			data = cli_conn.recv(1024) # check buffer limit
			print 'data:', data

			data = 'received: ' + data
			#self.treatMessage(self, data)

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
		
bankObject=Bank()	