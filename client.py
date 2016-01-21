import requests
import uuid
import json
import os
import time

def doWork(server,apikey):
	# GET WORK
	r = requests.get(server,{'apikey':apikey})
	data = json.loads(r.text)

	if 'No more work' in data['message']:
		return False

	# RUN PROGRAM
	t0 = time.time()
	with open('temp.fa','w') as f:
		for i in range(len(data['sequences'])):
			f.write('>' + str(i) + '\n')
			f.write(data['sequences'][i] + '\n')
	os.system('blastp -db nr -query temp.fa -num_threads 4 -out out.txt -num_alignments 0 -num_descriptions 200000 -task blastp-fast')
	print('Calculated data in ' + str(time.time()-t0))

	# ANALYZE OUTPUT
	inSequences = False
	numSequences = 0
	nums = []
	with open('out.txt','r') as f:
		for line in f:
			if 'Lambda' in line and 'K' in line and 'alpha' in line and numSequences > 0:
				inSequences = False
				nums.append(numSequences)
				numSequences = 0
			if inSequences and len(line)>5:
				numSequences += 1
			if 'Sequences producing significant alignments' in line:
				inSequences = True

	os.remove('out.txt')
	# POST WORK
	payload = {'apikey':apikey,'sequences':nums}
	r = requests.post(server,data = json.dumps(payload))
	data = json.loads(r.text)
	print(data)

	# GET MORE WORK
	return True


if __name__ == '__main__':
	apikey = str(uuid.uuid4()).replace('-','')
	server = 'http://ips.colab.duke.edu:8234/'
	stillWorkToDo = True
	while stillWorkToDo:
		stillWorkToDo = doWork(server,apikey)


