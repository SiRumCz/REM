for compress large database file into each chunk, use `tar cvzf - dep_network_npm_search.db | split --bytes=80MB - dep_network_npm_search.db.tar.gz.`

for uncompress files into one, use `cat dep_network_npm_search.db.tar.gz.a* | tar xzvf -`

