### Ripple Effect of Metrics dependency graph

The Ripple Effect of Metrics (REM) graph is a dependency graph designed to help developers identify vulnerable dependencies with lower metric-rating transitive dependencies in their dependency chains.

demo: http://turingmachine.org/rem_demo/

### Instruction

#### description

- `preprocess.py` creates data for NPM packages and scores.
- `rem_graph_run_single.py` generates single REM graph
    - `<keyword>` is metric of health: popularity, quality, maintenance, final. 
    - `filter=True|False` toggles the graph filtering.
    - `<github_url>` is the github repo link to the NPM application to be analyzed.
    - `[<out_folder>(htmls/)]` is the output folder for rendered graph, optional.
- `rem_graph_run_all.py` generates both full and filtered REM graphs for all four metrics
    - `<github_url>` is the github repo link to the NPM application to be analyzed.
    - `[<out_folder>(htmls/)]` is the output folder for rendered graph, optional.

#### Docker container

The Docker container includes every environment for REM graph rendering.

 - Docker requirment: >= 10GB memory
 - under current directory, run `docker build .`
 - once the build is finished, run `docker run -it <build id>`
 - in the CLI, run `python3 rem_graph_run_all.py <github_url>` to generate all 8 REM graphs, or run `python3 rem_graph_run_single.py <keyword> filter=True|False <github_url> [<out_folder>(htmls/)]` tp generate single REM graph
 - graphs will be created in `/htmls` folder
 - to export file from docker to local, keep the container running and run `docker cp <container id>:/htmls <target_dir>` from host
