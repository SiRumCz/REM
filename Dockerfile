FROM ubuntu

# npm packages/dependency relationships/metrics database
COPY data/dep_network_npm_search.db /data/dep_network_npm_search.db
# requirements.txt
COPY requirements.txt /requirements.txt
# preprocessing script
COPY preprocess.py /preprocess.py
# single REM generator script
COPY rem_graph_run_single.py /rem_graph_run_single.py
# all REM generator script
COPY rem_graph_run_all.py /rem_graph_run_all.py

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