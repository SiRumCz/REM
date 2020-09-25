FROM ubuntu

# npm packages/dependency relationships/metrics database
COPY data/dep_network_npm_search.db /data/dep_network_npm_search.db
# requirements.txt
COPY requirements.txt /requirements.txt
# preprocessing script
COPY preprocess.py /preprocess.py
# REM generator scripts
COPY utils.py /utils.py
COPY rem_filter.py /rem_filter.py
COPY rem_graph_analysis.py /rem_graph_analysis.py
COPY rem_graphics.py /rem_graphics.py
COPY rem_graph_run_single.py /rem_graph_run_single.py
COPY rem_graph_run_all.py /rem_graph_run_all.py
COPY plain_graph_run.py /plain_graph_run.py

# output folder
RUN mkdir /htmls
# linux environments
RUN apt-get -y update
RUN apt-get -y install software-properties-common
RUN apt-add-repository universe
RUN apt-get -y install python3-pip graphviz
# python environments
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt