from sys import platform
print(f'os platform: {platform}')
if platform == 'win32':
  NPMDB='data\\dep_network_npm_search.db' # sqlite3 NPM dependency database
  NPMJSON='data\\npm_graph.json'
else:
  NPMDB='data/dep_network_npm_search.db'
  NPMJSON='data/npm_graph.json'
NPMGRAPH_LOAD=False
JSONMODE=False
FILTER_ENABLE=True