#!/usr/bin/python

commonAlreadyHere=True

import string
import random
import socket
import re
import sys
from decimal import *
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

rand=random.SystemRandom()
getcontext().prec = 20

class ret255(Exception):
	pass

class ret63(Exception):
	pass

class ret0(Exception):
	pass

LENGTH_OF_ALL_PLAINTEXTS = 336

def sendMessage(conn, pText, sEncryptionKey, sSignatureKey):
	tx = pText
	tx += ' pad=x'
	tx += rand.choice(string.ascii_letters)*(LENGTH_OF_ALL_PLAINTEXTS-len(tx))

	def encrypt(plainText):
		iv = Random.new().read(AES.block_size)
		cipher = AES.new(sEncryptionKey, AES.MODE_CBC, iv)
		cipherText = iv + cipher.encrypt(plainText)
		return cipherText

	def signMessage(message):
		h = SHA.new(message)
		signer = PKCS1_v1_5.new(sSignatureKey)
		signature = signer.sign(h)
		return message + signature

	conn.send(signMessage(encrypt(tx)))

def receiveMessage(conn, sEncryptionKey, sSignatureKey):
	messageReceived = conn.recv(609)

	def checkSignature(message, signature):
		h = SHA.new(message)
		verifier = PKCS1_v1_5.new(sSignatureKey)

		if verifier.verify(h, signature):
			return message
		else:
			raise ret63

	def decrypt(cipherText):
		iv = cipherText[0: AES.block_size]
		cipher = AES.new(sEncryptionKey, AES.MODE_CBC, iv)
		return cipher.decrypt(cipherText[AES.block_size:])

	if len(messageReceived):
		try:
			return msgParse(decrypt(checkSignature(messageReceived[0:352], messageReceived[352:])))
		except:
			raise ret63

def debug(s):
	#print(s) #change to 'pass' to deliver.
	pass
	sys.stdout.flush()
	
def msgParse(msgPayload):
	try:
		validTitles=['atmID',
					 'timestamp',
					 'replyTo',
					 'bankAns',
					 'action',
					 'atmAns',
					 '$',
					 'account',
					 'pad',
					 'pin']

		fields=msgPayload.split()
		fieldsTuples=[f.split('=') for f in fields]
		fieldsDict = {ft[0]:ft[1] for ft in fieldsTuples}

		assert all(t in validTitles for t in fieldsDict)
		return fieldsDict
	except:
		raise ret63

def validateNumbers(number):
	if not re.match('^(0|[1-9][0-9]*)$', number):
		raise ret255

def validateCurrencyNumbers(number):
	vNumber = number.split('.')

	if len(vNumber) != 2:
		raise ret255

	if not re.match('^(0|[1-9][0-9]*)$', vNumber[0]):
		raise ret255

	if not re.match('^[0-9]{2}$', vNumber[1]):
		raise ret255

def validatePortNumber(port):
	if port < 1024 or port > 65535:
		raise ret255

def validateFileName(fileName):
	if fileName == '.' or fileName == '..':
		raise ret255

	if not re.match('^[_\-\.0-9a-z]{1,255}$', fileName):
		raise ret255

def validateIPAddress(sIP):
	vIP = sIP.split('.')

	if len(vIP) != 4:
		raise ret255
	else:
		for block in vIP:
			validateNumbers(block)
			if int(block) < 0 or int(block) > 255:
				raise ret255

def validateAccountName(sAccount):
	if len(sAccount) < 1 or len(sAccount) > 255:
		raise ret255

def validateAmount(amount):
	if amount < Decimal('0.00') or amount > Decimal('4294967295.99'):
		raise ret255

def validateBankAnswer(reply, atmID, timestamp):
	if reply['bankAns'] == 'n':
		debug('Error in operation')
		raise ret255
	elif reply['timestamp'] != timestamp:
		debug('Error in timestamp validation')
		raise ret255
	elif reply['atmID'] != atmID:
		debug('Error in atm validation')
		raise ret255
