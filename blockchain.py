import hashlib, json, sys, random, copy

#HASHING HELPER
def hashMe(msg=""):
    if type(msg) != str:
        msg = json.dumps(msg, sort_keys=True)
    if sys.version_info.major == 2:
        return unicode(hashlib.sha256(msg).hexdigest(), 'utf-8')
    else:
        return hashlib.sha256(str(msg).encode('utf-8')).hexdigest()
    

#TRANSACTION GENERATOR

random.seed(0)

def makeTransaction(maxValue=3):
    sign = int(random.getrandbits(1)) * 2 - 1
    amount = random.randint(1, maxValue)
    alicePays = sign * amount
    bobPays = -1 * alicePays
    return {'Alice': alicePays, 'Bob': bobPays}

#TRANSACTION BUFFER

txnBuffer = [makeTransaction() for i in range(30)]

#STATE UPDATE AND VALIDATION

def updateState(txn, state):
    state = state.copy()
    for key in txn:
        if key in state.keys():
            state[key] += txn[key]
        else:
            state[key] = txn[key]
    return state

def isValidTxn(txn, state):
    if sum(txn.values()) != 0:
        return False
    for key in txn.keys():
        acctBalance = state.get(key, 0)
        if (acctBalance + txn[key]) < 0:
            return False
    return True

#GENESIS BLOCK CREATION

state = {'Alice': 50, 'Bob': 50}
genesisBlockTxns = [state]
genesisBlockContents = {
    'blockNumber': 0,
    'parentHash': None,
    'txnCount': 1,
    'txns': genesisBlockTxns
}
genesisHash = hashMe(genesisBlockContents)
genesisBlock = {
    'hash': genesisHash,
    'contents': genesisBlockContents
}
chain = [genesisBlock]

#BLOCK CREATER

def makeBlock(txns, chain):
    parentBlock = chain[-1]
    parentHash = parentBlock['hash']
    blockNumber = parentBlock['contents']['blockNumber'] + 1
    txnCount = len(txns)
    blockContents = {
        'blockNumber': blockNumber,
        'parentHash': parentHash,
        'txnCount': txnCount,
        'txns': txns
    }
    blockHash = hashMe(blockContents)
    block = {'hash': blockHash, 'contents': blockContents}
    return block


#BUILD THE BLOCKCHAIN

blockSizeLimit = 5

while len(txnBuffer) > 0:
    txnList = []
    while (len(txnBuffer) > 0) and (len(txnList) < blockSizeLimit):
        newTxn = txnBuffer.pop()
        if isValidTxn(newTxn, state):
            txnList.append(newTxn)
            state = updateState(newTxn, state)
        else:
            print("Ignored invalid transaction.")
    block = makeBlock(txnList, chain)
    chain.append(block)


#CHAIN VALIDATION

def checkBlockHash(block):
    expectedHash = hashMe(block['contents'])
    if block['hash'] != expectedHash:
        raise Exception('Invalid block hash at block %s' % block['contents']['blockNumber'])

def checkBlockValidity(block, parent, state):
    parentNumber = parent['contents']['blockNumber']
    parentHash = parent['hash']
    blockNumber = block['contents']['blockNumber']
    
    for txn in block['contents']['txns']:
        if isValidTxn(txn, state):
            state = updateState(txn, state)
        else:
            raise Exception('Invalid transaction in block %s: %s' % (blockNumber, txn))

    checkBlockHash(block)

    if blockNumber != (parentNumber + 1):
        raise Exception('Incorrect block number at block %s' % blockNumber)
    if block['contents']['parentHash'] != parentHash:
        raise Exception('Incorrect parent hash at block %s' % blockNumber)
    
    return state

def checkChain(chain):
    if isinstance(chain, str):
        chain = json.loads(chain)
    state = {}
    for txn in chain[0]['contents']['txns']:
        state = updateState(txn, state)
    checkBlockHash(chain[0])
    parent = chain[0]
    for block in chain[1:]:
        state = checkBlockValidity(block, parent, state)
        parent = block
    return state


#Simulate Node Receiving a New Block

nodeBchain = copy.copy(chain)
nodeBtxns = [makeTransaction() for i in range(5)]
newBlock = makeBlock(nodeBtxns, nodeBchain)

try:
    print("New Block Received; Checking...")
    state = checkBlockValidity(newBlock, chain[-1], state)
    chain.append(newBlock)
    print("Block accepted. Chain length:", len(chain))
except:
    print("Invalid block. Rejected.")


#OUTPUT CHECKING

print("Final State:", checkChain(chain))