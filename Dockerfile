FROM ubuntu

# database
COPY data/dep_network_npm_search.db /data/dep_network_npm_search.db
# python environment
COPY requirements.txt /requirements.txt
# prprocess script
COPY preprocess.py /preprocess.py
# single REM generator script
COPY rem_graph_run_single.py /rem_graph_run_single.py
# all REM generator script
COPY rem_graph_run_all.py /rem_graph_run_all.py

RUN mkdir /htmls 
RUN apt-get -y update
RUN apt-get -y install software-properties-common
RUN apt-add-repository universe
RUN apt-get -y install python3-pip graphviz

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt