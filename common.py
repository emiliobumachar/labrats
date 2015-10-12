import string
import random
import socket
import re
import sys
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

rand=random.SystemRandom()

class ret255(Exception):
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
		#debug('iv+cipher len:' + str(len(cipherText)))
		return cipherText

	def signMessage(message):
		h = SHA.new(message)
		signer = PKCS1_v1_5.new(sSignatureKey)
		signature = signer.sign(h)
		#debug('signature len:' + str(len(signature)))
		return message + signature

	debug('messageSent: ' + tx)

	conn.send(signMessage(encrypt(tx)))

def receiveMessage(conn, sEncryptionKey, sSignatureKey):
	messageReceived = conn.recv(609)

	def checkSignature(message, signature):
		h = SHA.new(message)
		verifier = PKCS1_v1_5.new(sSignatureKey)

		if verifier.verify(h, signature):
			debug('The signature is authentic')
			return message
		else:
			debug('The signature is not authentic')
			raise ret255

	def decrypt(cipherText):
		iv = cipherText[0: AES.block_size]
		cipher = AES.new(sEncryptionKey, AES.MODE_CBC, iv)
		return cipher.decrypt(cipherText[AES.block_size:])

	if len(messageReceived):
		print messageReceived
		return msgParse(decrypt(checkSignature(messageReceived[0:352], messageReceived[352:])))
	
def debug(s):
	print(s) #change to 'pass' to deliver.
	sys.stdout.flush()
	
def msgParse(msgPayload):
	#Returns a dictionary with the field titles as keys. Raises an error if signature does not match, decryption fails, or invalid field.
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

	#debug('fieldsDict:' + str(fieldsDict))

	assert all(t in validTitles for t in fieldsDict)
	return fieldsDict

def validateNumbers(number):
	if not re.match('^(0|[1-9][0-9]*)$', number):
		raise ret255

def validatePortNumber(port):
	if port < 1024 or port > 65535:
		raise ret255

def validateFileName(fileName):
	if fileName == '.' or fileName == '..':
		raise ret255

	if not re.match('^[_\-\.0-9a-z]{1,255}$', fileName):
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