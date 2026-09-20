import subprocess
from typing import List, Optional


def find_conda_environments() -> List[str]:
	''' return names of conda environments available on system  '''
	try:
		result = subprocess.run(
			['conda', 'env', 'list'],
			capture_output = True, text = True, check = True
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

		if not parts: 
			continue

		# ignore '*' marker used for active environments
		if parts[0] == '*':
			if len(parts) >= 2:
				environments.append(parts[1])

		else:
			environments.append(parts[0])

	

	return environments



def find_environment_for_module(module_name: str,) -> Optional[str]:
	''' search all CONDA environments for a Python module, if installed.'''

	environments = find_conda_environments()

	print('CONDA environments found:')
	print(environments)

	for env in environments:

		print(f"Checking {env} "
			f"for module {module_name}...")

		try:
			result = subprocess.run(['conda','run','-n',env,'python','-c',f"import {module_name}"], capture_output=True, text=True)

			if result.returncode == 0:
				print(f"Found {module_name} "
					f"in {env}")
				return env

			if result.stderr:
				print(result.stderr)

		except FileNotFoundError:
			return None

	return None





