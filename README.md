### deprecation-ripples

Expose dependnecy health and ripple effect of dependency deprecation using hierarchical dependency graph for NPM software applications.

### Instruction

#### description

- `preprocess.py` creates data for NPM packages and scores.
- `rem_graph_run_single.py` generates single REM graph:
    - `<keyword>` is metric of health: popularity, quality, maintenance, final. 
    - `filter=True|False` toggles the graph filtering.
    - `<github_url>` is the github repo link to the NPM application to be analyzed.
    - `[<out_folder>(htmls/)]` is the output folder for rendered graph, optional.
- `rem_graph_run_all.py` generates both full and filtered REM graphs for all four metrics:
    - `<github_url>` is the github repo link to the NPM application to be analyzed.
    - `[<out_folder>(htmls/)]` is the output folder for rendered graph, optional.

#### Docker container

The Docker container includes every environment for REM graph rendering.

 - Docker requirment: >= 10GB memory
 - under current directory, run `docker build .`
 - once the build is finished, run `docker run -it <build id>`
 - in the CLI, run `python3 rem_graph_run_all.py <github_url>`
 - graphs will be created in `/htmls` folder
 - to export file from docker to local, keep the container running and run `docker cp <container id>:/htmls <target_dir>` from host
