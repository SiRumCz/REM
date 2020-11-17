from sys import platform
print(f'os platform: {platform}')
if platform == 'win32':
  NPMRAW='' # raw npm doc file
  NPMDB='data\\dep_network_npm_search.db' # sqlite3 NPM dependency database
  NPMJSON='data\\npm_graph.json'
else:
  NPMRAW='' 
  NPMDB='data/dep_network_npm_search.db'
  NPMJSON='data/npm_graph.json'
NPMGRAPH_RELOAD=False
JSONMODE=False
FILTER_ENABLE=True
# rem settings for security advisory dependabot
REM_HOST='localhost:5000'
# REM_DEPENDABOT_HTML_OUTDIR='../public_html/dependabot-rem/live'
# REM_DEPENDABOT_IMG_OUTDIR='../public_html/dependabot-rem/img'
REM_DEPENDABOT_HTML_OUTDIR='test\\live'
REM_DEPENDABOT_IMG_OUTDIR='test\\img'