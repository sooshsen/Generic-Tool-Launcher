import subprocess
from typing import List

def find_conda_environments() -> List[str]:
	'''
	return the names of conda environments available on the system 
	'''
	try:
		result = subprocess.run(
			['conda', 'env', 'list'],
			capture_output = True,
			text = True,
			check = True
			)
	except (subprocess.CalledProcessError, FileNotFoundError):
		return []



	environments = []



	for line in result.stdout.splitlines():
		line = line.strip()

		# ignore comments and empty lines
		if not line or line.startswith('#'):
			continue

		# conda environment lines normallly look like:
		# 
		# base			C:/.../anaconda3
		# deeplabcut	C:/.../envs/deeplabcut
		# 
		parts = line.split()

		if parts:
			environment_name = parts[0]

			if environment_name != '*':
				environments.append(environment_name)

	return environments
