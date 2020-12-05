from flask import Flask, jsonify, request

from preprocess import run_preprocess, update_raw_doc_from_api
from rem_graph_dependabot import create, create_dependabot_pr_rem_subgraph

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, welcome to Ripple-Effect of Metrics (github.com/SiRumCz/REM)."


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


@app.route('/rem-highlight', methods = ['POST'])
def rem_highlight():
    """
    Creates filtered Ripple-Effect of Metrics that highlights packages
    {
        pr_link: http://.../.img,
        live_link: http://.../.html
    }
    """
    packages = request.form.getlist('packages')
    depfile = request.form['depfile']
    pr_link, live_link = create(packages=packages, depfile=depfile)
    return jsonify({'pr_link': pr_link, 'live_link':live_link})


@app.route('/rem-vulnerable-with-lockfile', methods = ['POST'])
def rem_vulnerable_with_lockfile():
    """
    Creates a plain Ripple-Effect of Metrics(security advisory) that highlights the dependencies
    that is, a sub-dependency graph using a lockfile ('package-lock.json' or 'npm-shrinkwrap.json')
    that has health metrics removed and only keep the ripple-effect metrics -- security advisory.
    @packages: vulnerable dependencies
    @
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


if __name__ == '__main__':
  app.run(debug = True)
