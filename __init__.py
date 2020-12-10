from flask import Flask, jsonify, request

from preprocess import run_preprocess, update_raw_doc_from_api
from rem_graph_dependabot import create, create_dependabot_pr_rem_subgraph, create_dependabot_issue_rem_graph

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, welcome to Ripple-Effect of Metrics (github.com/sirumcz/rem)."


@app.route('/update-raw-doc')
def update_raw_doc():
    try:
        # update_raw_doc_from_api()
        return 'success'
    except:
        return 'fail'


@app.route('/update-npm-database', methods = ['GET'])
def update_npm_database():
    """
    UNSAFE - NOT TESTED
    """
    # run_preprocess()
    return 'success'


@app.route('/rem-vulnerable-with-lockfile', methods = ['POST'])
def pr_rem_vulnerable_with_lockfile():
    """
    Creates a plain Ripple-Effect of Metrics(security advisory) that highlights the dependencies
    that is, a sub-dependency graph using a lockfile ('package-lock.json' or 'npm-shrinkwrap.json')
    that has health metrics removed and only keep the ripple-effect metrics -- security advisory.
    @params:
        - packages: vulnerable dependencies
        - package_json: package.json content
        - lockfile: lockfile content
    @return:
    {
        pr_link: http://.../.img,
        live_link: http://.../.html
    }
    """
    packages = request.form.getlist('packages')
    package_json = request.form['package_json']
    lockfile = request.form['lockfile']
    pr_link, live_link = create_dependabot_pr_rem_subgraph(packages=packages, package_json=package_json, lockfile=lockfile)
    return jsonify({'pr_link': pr_link, 'live_link':live_link})


@app.route('/rem-with-lockfile-for-issue', methods = ['POST'])
def issue_rem_with_lockfile():
    """
    Creates a Ripple-Effect of Metrics(security advisory) that highlights the dependencies health,
    that is, a complete dependency graph using a lockfile ('package-lock.json' only)
    NOTE: npm-shrinkwrap.json is not supported.
    @params:
        - package_json: package.json content
        - lockfile: lockfile content
        - highlight_metric: selections from [final, popularity, quality, maintenance] from NPM search scores
    @return:
    {
        issue_link: http://.../.img,
        live_link: http://.../.html
    }
    """
    package_json = request.form.get('package_json')
    lockfile = request.form.get('lockfile')
    highlight_metric = request.form.get('highlight_metric')
    issue_link, live_link = create_dependabot_issue_rem_graph(package_json=package_json, lockfile=lockfile, highlight_metric='final')
    return jsonify({'issue_link': issue_link, 'live_link':live_link})


if __name__ == '__main__':
  app.run(debug = True)
