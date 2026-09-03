from pathlib import Path
from PySide6.QtWidgets import (
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QLabel,
	QPushButton,
	QMessageBox,
	QFrame
	)

from .conda_manager import find_conda_environments
from .tool_registry import ToolRegistry
from .process_runner import launch_conda_command


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()  # ??

		self.setWindowTitle('Generic Tool Launcher')
		self.resize(900, 600)

		self.registry = ToolRegistry(
			Path(__file__).parent.parent / "programs"
			)

		self.setup_ui()


	def setup_ui(self):
		central_widget = QWidget()
		self.setCentralWidget(central_widget)

		layout = QVBoxLayout(central_widget)

		# title
		title = QLabel('Generic Tool Launcher')
		title.setStyleSheet('''
			QLabel {
				font-size: 28px;
				font-weight: bold;
				padding: 10px;
			}
			''')

		layout.addWidget(title)

		# subtitle
		subtitle = QLabel(
			'Launch scientific analysis tools from their respective Conda environments.'
			)

		subtitle.setStyleSheet('''
			QLabel {
				font-size: 14px;
				color: #666666;
				padding: 0 10px 15px 10px;
			}
			''')

		layout.addWidget(subtitle)

		'''
		# deeplabcut
		dlc_card = self.create_tool_card(
			'DeepLabCut',
			'Pose estimation and animal tracking',
			'DEEPLABCUT'
			)

		layout.addWidget(dlc_card)

		# simBA
		simba_card = self.create_tool_card(
			'SimBA',
			'Simple behavior annotation and analysis',
			'simBA'
			)

		layout.addWidget(simba_card)
		'''

		# load tools from YAML files
		tools = self.registry.load_tools()

		for tool in tools:
			tool_card = self.create_tool_card(tool)

			layout.addWidget(tool_card)


		# settings
		settings_button = QPushButton('Settings')
		
		settings_button.clicked.connect(self.show_settings)

		layout.addWidget(settings_button)
		layout.addStretch()



	def create_tool_card(self, tool):

		name = tool['name']
		description = tool['description']
		environment = tool['environment']

		frame = QFrame()
		frame.setFrameShape(QFrame.Shape.StyledPanel)

		layout = QVBoxLayout(frame)

		title = QLabel(name)

		title.setStyleSheet('''
			QLabel {
				font-size: 20px;
				font-weight: bold;
			}
			''')

		layout.addWidget(title)

		description_label = QLabel(description)

		layout.addWidget(description_label)

		environment_label = QLabel(
			f'Conda environment: {environment}'
			)

		layout.addWidget(environment_label)

		button = QPushButton(f'Open {name}')

		button.clicked.connect(
			lambda: self.open_tool(tool)
			)

		layout.addWidget(button)

		return frame


	def open_tool(self, tool):

		name = tool['name']
		environment = tool['environment']

		environments = find_conda_environments()

		if environment not in environments:

			QMessageBox.warning(
				self,
				'Environment not found',
				(
					f"The Conda environment '{environment}'"
					f"was not found.\n\n"
					f"Available environments: \n"
					+ "\n".join(environments)
					),
				)
			return

		command = tool['launch']['command']

		try:
			launch_conda_command(
				environment,
				command,
			)

		except Exception as error:

			QMessageBox.critical(
				self,
				f"Could not start {name}",
				str(error),
			)

		'''
		QMessageBox.information(
			self,
			name,
			(
				f"{name} is configured correctly.\n\n"
				f"Conda environment: \n{environment}"
				),
			)
		'''

	def show_settings(self):

		environments = find_conda_environments()

		QMessageBox.information(
			self,
			'Conda environments',
			"Available Conda environments: \n\n"
			+ "\n".join(environments)
			)












