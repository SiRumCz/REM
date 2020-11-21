from flask import Flask, jsonify, request

from preprocess import run_preprocess, update_raw_doc_from_api
from rem_graph_dependabot import create

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, welcome to Ripple-Effect of Metrics (github.com/SiRumCz/REM)."


@app.route('/update-raw-doc')
def update_raw_doc():
    try:
        update_raw_doc_from_api()
        return 'success'
    except:
        return 'fail'


@app.route('/update-npm-database', methods = ['GET'])
def update_npm_database():
    """
    UNSAFE - NOT TESTED
    """
    run_preprocess()
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


if __name__ == '__main__':
  app.run(debug = True)
