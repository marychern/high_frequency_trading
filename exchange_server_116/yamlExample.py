# used example from custom_otree_config.py
# how to install yaml: https://codeyarns.com/2017/03/21/how-to-deal-with-yaml-in-python/

import yaml
import sys

# def from_yaml(cls, path_to_file) -> dict

path_to_file = "yamlExample.yaml"
with open(path_to_file, 'r') as f:
	try:
		configs = yaml.load(f)
	except yaml.YAMLError as e:
		raise e
	#else:
		#log.debug('custom config: %s.' % path_to_file)
		
	# prints to the standard output, whatever is in yaml file	
	# we can change location to another file if we want to dump
	# the changes we made to the dictionaries in the yaml file
	
	yaml.dump(configs, sys.stdout)
	# print configs -> also works as well
	
# return cls(configs, path_to_file)
	
# ________ OTHER NEED TO KNOWS FOR LATER _________________________	

	# can be used to print key and value of a dictionary in yaml file
		# for key, value in yaml.load(open(path_to_file))['parameters'].iteritems():
			# print key, value
	
	# use this to change the values in the dictionary of the yaml file 
		# txt = configs["market"]["auction-format"] = value
		# print txt
		
	# use this to insert into the yaml file at index 1 in dictionary
		# data = yaml.load(file)
		# data.insert(1, 'last name', 'Bob', comment = "new key") 
		
		
