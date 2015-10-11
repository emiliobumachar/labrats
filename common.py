import string
import random
import socket
import re

rand=random.SystemRandom()

class ret255(Exception):
	pass
LENGTH_OF_ALL_PLAINTEXTS = 333

def sendPlainText(conn, pText):
	tx=pText
	tx+=' pad=x'
	tx+=rand.choice(string.ascii_letters)*(LENGTH_OF_ALL_PLAINTEXTS-len(tx))
	conn.send(tx)

	reply = conn.recv(4096)
	return msgParse(reply)
	
def debug(s):
	print(s) #change to 'pass' to deliver.
	
def msgParse(msgPayload):
	'''Returns a dictionary with the field titles as keys. Raises an error if signature does not match, decryption fails, or invalid field.'''
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
	def checkSignature(blob):
		return blob
	def decrypt(blob):
		return blob
	plainText=decrypt(checkSignature(msgPayload))
	fields=plainText.split()
	fieldsTuples=[f.split('=') for f in fields]
	fieldsDict = {ft[0]:ft[1] for ft in fieldsTuples}

	debug('fieldsDict:' + str(fieldsDict))

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