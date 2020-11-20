from sys import platform
print(f'os platform: {platform}')
if platform == 'win32':
  NPMRAW='' # raw npm doc file
  NPMDB='data\\dep_network_npm_search.db' # sqlite3 NPM dependency database
  NPMJSON='data\\npm_graph.json'
else:
  NPMRAW=''
  NPMDB='/var/www/FlaskApp/REM/data/dep_network_npm_search.db'
  NPMJSON='/var/www/FlaskApp/REM/data/npm_graph.json'
NPMGRAPH_RELOAD=False
JSONMODE=False
FILTER_ENABLE=True
# rem settings for security advisory dependabot
REM_DEPENDABOT_HTML_URL='http://helium.cs.uvic.ca/rem/live-view'
REM_DEPENDABOT_IMG_URL='http://helium.cs.uvic.ca/rem/images'
REM_DEPENDABOT_HTML_OUTDIR='/var/www/FlaskApp/REM/live-view'
REM_DEPENDABOT_IMG_OUTDIR='/var/www/FlaskApp/REM/images'
