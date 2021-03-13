from sys import platform
print(f'os platform: {platform}')
if platform == 'win32':
  NPMRAW='' # raw npm doc file
  NPMDB='data\\dep_network_npm_search.db' # sqlite3 NPM dependency database
  NPMJSON='data\\npm_graph.json'
else:
  #NPMRAW=''
  NPMRAW='/var/www/FlaskApp/REM/data/REM-dataset/replicate_npm_all_doc_include_true'
  NPMDB='/var/www/FlaskApp/REM/data/dep_network_npm_search.db'
  NPMJSON='/var/www/FlaskApp/REM/data/npm_graph.json'
NPMRAW_API='https://replicate.npmjs.com/_all_docs?include_docs=true'
NPMGRAPH_RELOAD=False
JSONMODE=False
FILTER_ENABLE=True
# rem settings for security advisory dependabot
REM_DEPENDABOT_HTML_URL='http://helium.cs.uvic.ca/rem/live-view'
REM_DEPENDABOT_IMG_URL='http://helium.cs.uvic.ca/rem/images'
# REM_DEPENDABOT_HTML_OUTDIR='/var/www/FlaskApp/REM/live-view'
# REM_DEPENDABOT_IMG_OUTDIR='/var/www/FlaskApp/REM/images'
# REM_DEPENDABOT_ISSUES_INDEX_TEMPLATE='/var/www/FlaskApp/REM/index_html.tmpl'
REM_DEPENDABOT_HTML_OUTDIR='live-view'
REM_DEPENDABOT_IMG_OUTDIR='images'
REM_DEPENDABOT_ISSUES_INDEX_TEMPLATE='index_html.tmpl'