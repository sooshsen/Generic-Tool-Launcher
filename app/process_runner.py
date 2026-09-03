import subprocess

def launch_conda_command(environment, command):
	'''
	Launch a command inside a specific Conda environment
	'''

	full_command = [
		'conda',
		'run',
		'-n',
		environment,
		*command,
	]

	print('Launching: ')
	print(' '.join(full_command))

	return subprocess.Popen(full_command)
