from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
#
# 
#
#
# -----------------------
# Encode/decode OUCH messages before/after they go through TCP connection
# Note! Notice the return statements


def decodeServerOUCH(data):
  header = chr(data[0]).encode('ascii')
  msg_type = OuchServerMessages.lookup_by_header_bytes(header)
  #print("\nDATA DECODESERVEROUCH:   \n",data[0:num_bytes])
  msg = msg_type.from_bytes(data[1:], header=False)
  return header, msg

"""
def decodeServerOUCH(data):
    return decodeServerRecursive(data, 0, 'NULL', 'NULL')
    #return header, msg

def decodeServerRecursive(data, start_idx, prev_header, prev_msg):
    header = chr(data[start_idx]).encode('ascii')
    if(doesHeaderNotExist(header)):
      return prev_header, prev_msg
    msg_type = OuchServerMessages.lookup_by_header_bytes(header)
    bytes_needed = bytes_needed(header)
    msg = msg_type.from_bytes(data[start_idx+1:bytes_needed], header=False)
    return decodeServerRecursive(data, start_idx+1+bytes_needed, header, msg)
"""
def decodeClientOUCH(data):
    header = chr(data[0]).encode('ascii')
    msg_type = OuchClientMessages.lookup_by_header_bytes(header)
    msg = msg_type.from_bytes(data[1:], header=False)
    return header, msg
