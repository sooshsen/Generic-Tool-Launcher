from pathlib import Path
import yaml

class ToolRegistry:

	def __init__(self, programs_directory):
		self.programs_directory = Path(programs_directory)

	def load_tools(self):
		tools = []

		for yaml_file in sorted(self.programs_directory.glob("*.yaml")):
			with open(yaml_file, "r", encoding="utf-8") as file:
				tool = yaml.safe_load(file)

			if tool:
				tool["_config_file"] = yaml_file

				tools.append(tool)

		return tools


