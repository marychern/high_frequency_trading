from OuchServer.ouch_messages import OuchClientMessages, OuchServerMessages
#
# 
#
#
# -----------------------
# Encode/decode OUCH messages before/after they go through TCP connection
# Note! Notice the return statements
# -----------------------
def bytes_needed(header):
  bytes_needed = 0
  if(header == 'S'):
    bytes_needed = 10
  elif(header == 'E'):
    bytes_needed = 40
  elif(header == 'C'):
    bytes_needed = 28
  elif(header == 'U'):
    bytes_needed = 80
  elif(header == 'A'):
    bytes_needed = 66
  elif(header == 'Q'):
    bytes_needed = 33
  else:
    bytes_needed = -1
    print("bytes_needed(): ERROR NO PROPER HEADER")
  return bytes_needed
    

def doesHeaderNotExist(header):
  if(header == 'S'):
    isExist = True
  elif(header == 'E'):
    isExist = True
  elif(header == 'C'):
    isExist = True
  elif(header == 'U'):
    isExist = True
  elif(header == 'A'):
    isExist = True
  elif(header == 'Q'):
    isExist = True
  else:
    isExist = False

  return isExist


def decodeServerOUCH(data):
  header = chr(data[0]).encode('ascii')
  msg_type = OuchServerMessages.lookup_by_header_bytes(header)
  num_bytes = bytes_needed(header)
#  print("\nDATA DECODESERVEROUCH:   \n",data[0:num_bytes])
  msg = msg_type.from_bytes(data[1:num_bytes], header=False)

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
