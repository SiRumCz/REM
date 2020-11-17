from flask import Flask, jsonify, request
from flask import g as flask_globals
from flask_cors import CORS

from preprocess import run_preprocess
from rem_graph_dependabot import create

app = Flask(__name__)
CORS(app)


@app.route('update-npm-database', methods = ['GET'])
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