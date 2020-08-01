### Ripple Effect of Metrics dependency graph

The Ripple Effect of Metrics (REM) graph is a dependency graph designed to help developers identify vulnerable dependencies with lower metric-rating transitive dependencies in their dependency chains.

sample:
![sample_rem](imgs/app_example_brackets_maintenance.png)

demo: http://turingmachine.org/rem_demo/

### How to run

#### Preparation

| Storage | RAM  | Language     | OS                                                          |
|---------|------|--------------|-------------------------------------------------------------|
| 2GB     | 10GB | Python 3.7.4 | Linux(Ubuntu 18.04)/MacOS(Catalina 10.15.5)/Windows 10 Home |

In this repository, we have provided a compressed database file that we generated on May, 2020. To uncompress it, run `cat dep_network_npm_search.db.tar.gz.a* | tar xzvf -`.

However, if you wish to obtain on latest data, run `python3 preprocess.py` to generate a database that contains the latest NPM pakcages and scores.

#### Run on local machine

1. Run `pip3 install -r requirements.txt` to install required Python libraries.
2. REM depends on GraphViz. To install it, go to https://graphviz.gitlab.io/download/ and look for right version for your OS.
3. Run `mkdir htmls` to create the folder that stores REM graphs.
4. `rem_graph_run_all.py` allows user to have all 8 REM graphs for four metrics of health (popularity, quality, maintenance, final) with and without Filtering. To run it, run `python3 rem_graph_run_all.py <github_url> [<out_folder>(htmls/)]` where `github_url` is the url to NPM application github repo, and optinal `out_folder` which is the output folder to store REM graphs, default is `htmls\`. For example, to generate every REM graph for [adobe/brackets](https://github.com/adobe/brackets), run `python3 rem_graph_run_all.py https://github.com/adobe/brackets`.
5. `rem_graph_run_single.py` allows user to generate REM graph on which metric of health and whether to use Filtering. To run it, run `python3 rem_graph_run_single.py <keyword> filter=True|False <github_url> [<out_folder>(htmls/)]` where `keyword` is one of the metrics of health (popularity, quality, maintenance, final), `filter=True|False` will toggle the graph filtering. For example, to generate a filtered REM graph with quality metric for [adobe/brackets](https://github.com/adobe/brackets), run `python3 rem_graph_run_single.py quality filter=True https://github.com/adobe/brackets`.
6. To view the REM graph generated, open it using a web browser (we recommend Chrome).

#### Run on local machine with Docker

The Dockerfile includes every environment for REM graph rendering.

1. Docker requirment: >= 10GB memory. Under `Preference -> Resources` of docker desktop, please set `Memory` to at least 10 GB.
2. under repo directory, run `docker build .` to build the image.
3. once the build is finished, run `docker run -it <image id>` where `image id` is the last string generated from the build. This command will bring the user to the CLI of the running Docker container for REM.
4. in the CLI, run `python3 rem_graph_run_all.py <github_url>` to generate all 8 REM graphs, or run `python3 rem_graph_run_single.py <keyword> filter=True|False <github_url> [<out_folder>(htmls/)]` tp generate single REM graph as what you would do on local machine
5. REM graphs will be created in `/htmls` folder inside Docker container
6. to export file from Docker container to local machine, keep the container running and run `docker cp <container id>:/htmls <target_dir>` from host. `container id` can be found by `docker ps`.
