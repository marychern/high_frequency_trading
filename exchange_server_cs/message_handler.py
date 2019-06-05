from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages

# -----------------------
# Encode/decode OUCH messages before/after they go through TCP connection
# Note! Notice the return statements
# -----------------------
def decodeServerOUCH(data):
    header = chr(data[0]).encode('ascii')
    msg_type = OuchServerMessages.lookup_by_header_bytes(header)
    msg = msg_type.from_bytes(data[1:], header=False)
    return header, msg

def decodeClientOUCH(data):
    print('data in decode is:{}'.format(data))
    header = chr(data[0]).encode('ascii')
    msg_type = OuchClientMessages.lookup_by_header_bytes(header)
    msg = msg_type.from_bytes(data[1:], header=False)
    return header, msg
