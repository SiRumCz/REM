NPM packages and scores database collected on May 2020 can be downloaded here: https://github.com/SiRumCz/REM-dataset

to compress large database file into each chunk, use `tar cvzf - dep_network_npm_search.db | split --bytes=80MB - dep_network_npm_search.db.tar.gz.`

to uncompress files into one, use `cat dep_network_npm_search.db.tar.gz.a* | tar xzvf -`

