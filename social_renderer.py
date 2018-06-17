''' 

Copyright 2018 Alexander Shuping

This file is part of Pysocial.

Pysocial is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pysocial is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pysocial.  If not, see <http://www.gnu.org/licenses/>.

'''

import networkx as nx
import pygraphviz as pgv

from social import database_io, configurer
from social_ui import ui, none_ui

class renderer:
	
	def __init__(self, db, config, ui=None):
		self.config = config
		self.db = db
		if ui:
			self.ui = ui
		else:
			self.ui = none_ui()

	def hook_ui(self, ui_to_hook):
		if ui_to_hook:
			self.ui = ui_to_hook
			return 0
		else:
			return 1
	
	def render(self, output_path, render_prog=None):
		if not self.db.is_connected():
			self.ui.log_error('Cannot render image while database is disconnected!')
			return 1

		if not self.db.current_file():
			self.ui.log_error('Cannot render when no file is open!')
			return 2

		nx_graph = nx.Graph()
		nodes = self.db.list_nodes()
		connections = self.db.list_connections()
		for node in nodes:
			nx_graph.add_node(node[1], label=node[0])

		for connection in connections:
			nx_graph.add_edge(connection[0], connection[1])

		pgv_graph = nx.drawing.nx_agraph.to_agraph(nx_graph)

		if render_prog:
			pgv_graph.draw(str(output_path),prog=render_prog)
		else:
			pgv_graph.draw(str(output_path),prog='circo')

		return 0
