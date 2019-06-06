import configargparse


p = configargparse.getArgParser()
p.add('--port', default=12345)
options, args = p.parse_known_args()

print('options:', options)
print(options.port)