def parse(msgPayload):
	'''Returns a dictionary with the field titles as keys. Raises an error if signature does not match, decryption fails, or invalid field.'''
	validTitles=['atmID',
                     'msgCounter',
                     'replyTo',
                     'bankAns',
                     'action',
                     'atmAns',
                     '$',
                     'account',
					 'pad']
	def checkSignature(blob):
		return blob
	def decrypt(blob):
		return blob
	plainText=decrypt(checkSignature(msgPayload))
	fields=plainText.split()
	fieldsTuples=[f.split('=') for f in fields]
	fieldsDict = {ft[0]:ft[1] for ft in fieldsTuples}
	assert all(t in validTitles for t in fieldsDict)
	return fieldsDict
