import logging
import copy
from itertools import groupby
import json
from flask import Flask, jsonify, request

app = Flask(__name__)
app.debug = False
sequences = {}
state = {}

# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

def fasta_iter(fasta_name):
    """
    given a fasta file. yield tuples of header, sequence
    """
    fh = open(fasta_name)
    # ditch the boolean (x[0]) and just keep the header or sequence since
    # we know they alternate.
    faiter = (x[1] for x in groupby(fh, lambda line: line[0] == ">"))
    fastas = []
    for header in faiter:
        # drop the ">"
        header = header.next()[1:].strip()
        # join all sequence lines to one.
        seq = "".join(s.strip() for s in faiter.next())
        if len(seq)>40 and len(seq)<600:
            fastas.append((header,seq))
    return fastas


@app.route('/', methods=['GET', 'POST'])
def add_message():
    logger = logging.getLogger('server')
    global state
    payload = {'success':True,'message':''}
    if request.method == 'POST':
        content = request.get_json(force=True)
        apikey = content['apikey']
        payload['message'] = 'Recieved content!'
        logger.info('Recieved content')
        logger.info(content)
        state['finished'].append(state['connected'][apikey]['ids'][0])
        data = {}
        data['name'] = state['connected'][apikey]['names'][0]
        data['ss'] = content['sequences']
        with open('data.json','a') as f:
            f.write(json.dumps(data) + '\n')
        state['doing'] = list(set(state['doing']) - set([state['connected'][apikey]['ids'][0]]))
        state['connected'].pop(apikey)
    else:
        logger.info('Recieved work request')
        possible = list(set(state['todo'])-set(state['finished'])-set(state['doing']))
        logger.info(str(len(possible)) + ' more sequences to analyze')
        if len(possible) == 0:
            payload['message'] = 'No more work!'
        else:
            apikey = request.args.get('apikey', '')
            payload['message'] = 'New data'
            payload['apikey'] = apikey
            work = []
            state['connected'][apikey] = {}
            state['connected'][apikey]['names'] = []
            state['connected'][apikey]['ids'] = []
            i = possible[0]
            work.append(sequences[i][1])
            state['connected'][apikey]['names'].append(sequences[i][0])
            state['connected'][apikey]['ids'].append(i)
            state['doing'].append(i)
            payload['sequences'] = work
            logger.info('Sent work')
            logger.info(payload)

    with open('state.json','w') as f:
        f.write(json.dumps(state))
    return jsonify(**payload)

if __name__ == '__main__':
    sequences = fasta_iter('1tit_similar.fa')
    try:
        state = json.load(open('state.json','r'))
    except:
        state = {}
        state['finished'] = []
    state['todo'] = range(len(sequences))
    state['doing'] = []
    state['connected'] = {}
    app.run(port=8235,host='ips.colab.duke.edu')
