from pathlib import Path
from PySide6.QtWidgets import QComboBox, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QFrame


from .conda_manager import find_environment_for_module
from .tool_registry import ToolRegistry
from .process_runner import ProcessRunner


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()  # ??

		self.setWindowTitle('Generic Tool Launcher')
		self.resize(600, 450)


		''' Store currently selected tool '''
		self.current_tool = None
		self.current_environment = None


		''' Load available tools '''
		self.registry = ToolRegistry(Path(__file__).resolve().parent.parent / "programs")
		# load tool definitions
		self.tools = self.registry.load_tools()

		
		''' Process Runner '''
		self.process_runner = ProcessRunner(self)

		self.process_runner.process_started.connect(self.tool_started)
		self.process_runner.process.finished.connect(self.tool_finished)
		self.process_runner.process_error.connect(self.tool_error)


		''' Main Widget '''
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		self.layout = QVBoxLayout(central_widget)



		''' Title '''
		title = QLabel('Generic Tool Launcher')
		title.setStyleSheet('''
				font-size: 24px; font-weight: bold; padding: 10px;
				''')
		self.layout.addWidget(title)



		''' Subtitle '''
		subtitle = QLabel('Launch scientific analysis tools from their respective Conda environments.')
		subtitle.setStyleSheet('''
				font-size: 14px; color: #666666; padding: 0 10px 15px 10px;
			''')
		self.layout.addWidget(subtitle)


		''' Program selector '''
		program_label = QLabel("Select program")

		self.layout.addWidget(program_label)
		self.program_dropdown = QComboBox()
		self.program_dropdown.addItem("Select a program...")

		for tool in self.tools:
			self.program_dropdown.addItem(tool['name'], tool)

		self.program_dropdown.currentIndexChanged.connect(self.program_changed)
		self.layout.addWidget(self.program_dropdown)
		

		''' Program card container '''
		self.program_container = QVBoxLayout()
		self.layout.addLayout(self.program_container)
        
		# Show initial message
		self.show_no_program_message("Select a tool to continue.")
		self.layout.addStretch()


	# ======================================================
	# Program selection
	# ======================================================
	def program_changed(self, index):
		''' called when user selects a tool '''

		self.clear_program_card()

		self.current_tool = None
		self.current_environment = None

		if index <= 0:
			self.show_no_program_message("Select a program to continue.")
			return

		tool = self.program_dropdown.itemData(index)

		if not tool:
			self.show_no_program_message("Selected program could not be loaded.")
			return

		self.show_program_card(tool)




	# ======================================================
	# Show program card
	# ======================================================
	def show_program_card(self, tool):
		''' display info about selected tool and search for its CONDA env'''

		self.current_tool = tool

		## CARD ##
		card = QFrame()
		card.setFrameShape(QFrame.StyledPanel)

		card.setStyleSheet("""
			border: 1px solid #cccccc; border-radius: 8px; padding: 10px;
			"""
			)

		card_layout = QVBoxLayout(card)
		card.setLayout(card_layout)


		## Program title ##
		name_label = QLabel(tool.get("name", "Unknown Program"))
		name_label.setStyleSheet("""
			font-size: 20px; font-weight: bold;
			"""
			)
		card_layout.addWidget(name_label)


		## DESCRIPTION ##
		description_label = QLabel(tool.get("description",""))
		description_label.setWordWrap(True)
		card_layout.addWidget(description_label)


		## DETECT PROGRAM ##
		detect_config = tool.get("detect", {})
		
		module_name = detect_config.get("python_module")
		if not module_name:
			warning_label = QLabel("No program detection method configured!")
			warning_label.setWordWrap(True)
			card_layout.addWidget(warning_label)

			status_label = QLabel("Status: Not configured")
			card_layout.addWidget(status_label)

			self.program_container.addWidget(card)

			return


		## SEARCH CONDA ENVS ##
		environment_label = QLabel("Searching CONDA environments...")
		card_layout.addWidget(environment_label)

		status_label = QLabel("Status: Searching")
		card_layout.addWidget(status_label)

		# add card before searching so user sees current status
		self.program_container.addWidget(card)


		## FIND ENV ##
		environment = find_environment_for_module(module_name)

		self.current_environment = environment
		if environment:
			environment_label.setText(f"Environment found: {environment}")
			status_label.setText("Status: Ready")

			# set launch button
			launch_button = QPushButton(f"Launch {tool['name']}")
			launch_button.clicked.connect(lambda: self.launch_tool(tool))
			card_layout.addWidget(launch_button)

		else:
			environment_label.setText("Environment found: None")
			
			warning_label = QLabel("Program not found in any CONDA environment.")
			warning_label.setWordWrap(True)
			card_layout.addWidget(warning_label)

			status_label.setText("Status: Not installed")



	# ======================================================
	# Launch Program
	# ======================================================
	def launch_tool(self, tool):
		''' launch selected program inside CONDA env '''

		environment = self.current_environment
		if not environment:
			QMessageBox.warning(self, "Environment Not Found", 
				(f"{tool['name']} was not found in any CONDA environment."))
			return

		launch_config = tool.get("launch", {})

		command = launch_config.get("command")
		if not command:
			QMessageBox.warning(self, "Launch Command Missing",
				(f"No launch command in configured for {tool['name']}."))
			return

		self.process_runner.start(environment, command)



	# ======================================================
	# Process Started
	# ======================================================
	def tool_started(self):
		''' called when the external program starts '''

		if self.current_tool:
			print(f"{self.current_tool['name']} started.")



	# ======================================================
	# Process Finished
	# ======================================================
	def tool_finished(self, exit_code):
		''' called when the external program exits '''

		if self.current_tool:
			print(f"{self.current_tool['name']}"
				f" finished with exit code {exit_code}.")



	# ======================================================
	# Process Error
	# ======================================================
	def tool_error(self, message):
		''' called when the QProcess encounters an error '''

		QMessageBox.critical(self, "Program Launch Error", message)



	# ======================================================
	# Clear program card
	# ======================================================
	def clear_program_card(self):
		''' remove everything in program card area '''

		while self.program_container.count():
			item = self.program_container.takeAt(0)
			widget = item.widget()

			if widget: 
				widget.deleteLater()
			else:
				child_layout = item.layout()

				if child_layout:
					self.clear_layout(child_layout)


	# ======================================================
	# Clear layout
	# ======================================================
	def clear_layout(self, layout):
		''' recursively clear a Qt layout '''

		while layout.count():
			item = layout.takeAt(0)
			widget = item.widget()

			if widget: 
				widget.deleteLater()
			else:
				child_layout = item.layout()

				if child_layout:
					self.clear_layout(child_layout)




	# ======================================================
	# No program message
	# ======================================================
	def show_no_program_message(self, message):
		''' display a message no program is selected '''

		label = QLabel(message)
		label.setWordWrap(True)
		label.setStyleSheet("""
			color: #666666; padding: 20px;
			"""
			)

		self.program_container.addWidget(label)










