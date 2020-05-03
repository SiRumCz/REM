'''
author: Kevin(Zhe) Chen
email: zkchen@uvic.ca

Description:
Preprocessing - retrieves data from raw npm data and store it into sqlite database 
with packages info, dependency relationships, and npms.io scores
'''
import sys # args
import sqlite3 # connection
import json # dump
import requests


def beautify_json(data:dict) -> str:
    '''
    beautify python dict to json format
    '''
    return json.dumps(data, indent=2)


def is_valid_key(data: dict, key) -> bool:
    '''
    check if key is valid
    '''
    return data and key and (key in data) and (data[key])

def create_tables(conn: sqlite3.Connection):
    dncur = conn.cursor()
    # packages - npm package meta data
    dncur.execute(''' DROP TABLE IF EXISTS packages; ''')
    dncur.execute(
        '''
        CREATE TABLE IF NOT EXISTS packages (
            name text PRIMARY KEY,
            latest text,
            author text,
            authoremail text,
            maintainers text,
            versions text,
            repotype text,
            repourl text,
            homepage text,
            license text,
            deprecated int,
            deprecatemessage text
        );
        '''
    )
    print('packages table created')
    # depend - dependency relationships
    dncur.execute(''' DROP TABLE IF EXISTS depend; ''')
    dncur.execute(
        ''' 
        CREATE TABLE depend (
            project_name text,
            project_ver text,
            depend_name text,
            depend_constraints text,
            FOREIGN KEY(project_name) REFERENCES packages(name)
        );
        '''
    )
    print('depend table created')
    # scores - npms.io score systems
    dncur.execute(''' DROP TABLE IF EXISTS scores; ''')
    dncur.execute(
        ''' 
        CREATE TABLE scores (
            name text,
            final real,
            popularity real,
            quality real,
            maintenance real,
            FOREIGN KEY(name) REFERENCES packages(name)
        ); 
        '''
    )
    print('scores table created')
    return conn.commit()


def update_packages_table(doc_file: str, conn: sqlite3.Connection) -> int:
    '''
    packages table stores the metadata extracted from NPM replicate registry
    '''
    dncur = conn.cursor()
    insert_query = ''' 
    INSERT INTO 
    packages(name, latest, author, authoremail, maintainers, 
    versions, repotype, repourl, homepage, license, deprecated, 
    deprecatemessage) 
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''

    index = 0
    total_num = 0
    with open(doc_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            index += 1
            # total number of packages from first line
            if index == 1:
                total_num = json.loads(line[:-10]+'}')['total_rows']
                continue
            # line limiter
            if index > total_num+1:
                break
            # trim
            if index < total_num+1:
                line = line[:-2]
            # package to be inserted
            package = {
                "name": None,
                "latest": None,
                "author": None,
                "authoremail": None,
                "maintainers": None,
                "versions": None,
                "repotype": None,
                "repourl": None,
                "homepage": None,
                "license": None,
                "deprecated": 0,
                "deprecatemessage": None
            }
            rawdata = json.loads(line)
            print("updating NPM packages metadata [{}/{}]".format(index-1, total_num), end='\r')
            if is_valid_key(rawdata, 'doc'):
                docdata = rawdata['doc'] # fetched doc data
                # print(beautifyJson(docdata))
                # package name
                if is_valid_key(docdata, 'name'):
                    package['name'] = str(docdata['name'])
                else:
                    package['name'] = str(rawdata['key'])
                # latest in dist-tags
                if is_valid_key(docdata, 'dist-tags') and is_valid_key(docdata['dist-tags'], 'latest'):
                    package['latest'] = str(docdata['dist-tags']['latest'])
                # author and author email
                if is_valid_key(docdata, 'author') and type(docdata['author']) is not str:
                    packageAuthor = docdata['author']
                    if is_valid_key(packageAuthor, 'name'):
                        package['author'] = str(packageAuthor['name'])
                    if is_valid_key(packageAuthor, 'email'):
                        package['authoremail'] = str(packageAuthor['email'])
                elif is_valid_key(docdata, 'author') and type(docdata['author']) is str:
                    package['author'] = str(docdata['author'])
                # maintainers: list of people who created this package
                if is_valid_key(docdata, 'maintainers'):
                    package['maintainers'] = str(docdata['maintainers'])
                # versions: only the dependency list of latest version
                # Alternative: list of all published versions (requires larger space)
                if is_valid_key(docdata, 'versions'):
                    versions = docdata['versions']
                    if is_valid_key(versions, package['latest']):
                        package_json = versions[package['latest']]
                    else:
                        # retrieve the last metadata from the versions
                        package_json = versions[list(versions.keys())[-1]]
                    if is_valid_key(package_json, 'dependencies'):
                        package['versions'] = json.dumps(package_json['dependencies'])
                # repo type and url
                if is_valid_key(docdata, 'repository') and type(docdata['repository']) is not str:
                    repo = docdata['repository']
                    if is_valid_key(repo, 'type'):
                        package['repotype'] = str(repo['type'])
                    if is_valid_key(repo, 'url'):
                        package['repourl'] = str(repo['url'])
                elif is_valid_key(docdata, 'repository') and type(docdata['repository']) is str:
                    package['repourl'] = str(docdata['repository'])
                # homepage
                if is_valid_key(docdata, 'homepage'):
                    package['homepage'] = str(docdata['homepage'])
                # license(s)
                if is_valid_key(docdata, 'license'):
                    package['license'] = str(docdata['license'])
                # deprecate state: 0: False, 1: True
                if is_valid_key(docdata, 'versions'):
                    latestdata = docdata['versions'][list(docdata['versions'].keys())[-1]]
                    if is_valid_key(latestdata, 'deprecated'):
                        package['deprecated'] = 1
                        package['deprecatemessage'] = str(latestdata['deprecated'])
                # do insert
                dncur.execute(insert_query, list(package.values()))
    print()
    return total_num


def update_depend_table(conn: sqlite3.Connection) -> int:
    '''
    extract dependency relationships from NPM data for only the latest version of the package
    example:
    package a has version v as its latest version, package a requires package b with version 
    constraint of ~1.0.0 and c with version constraint of ^1.0.0 , in database these dependency 
    relationships will be shown as: 
    project_name  project_version  depend_name  depend_constraint
    a             v                b            ~1.0.0
    a             v                c            ^1.0.0
    '''
    dncur = conn.cursor()
    # get full list of package versions
    dncur.execute(''' SELECT name, latest, versions FROM packages; ''')
    num_deps = 0
    for deps in dncur.fetchall():
        name, latest, version = deps
        if version:
            packagejson_dep = json.loads(version)
            for k, v in packagejson_dep.items():
                num_deps += 1
                k = str(k)
                v = str(v)
                dncur.execute(''' INSERT INTO depend VALUES (?, ?, ?, ?); ''', (name, latest, k, v))
                print('updating NPM dependency relationships [{}]'.format(num_deps), end='\r')
    print()
    return num_deps


def post_api_data(url: str, data: str):
    '''
    retrieve POST requests from url
    '''
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        resp = requests.post(url, headers=headers, data=data)
        return resp
    except:
        return None


def get_api_data(url: str):
    '''
    retrieve GET requests from url
    '''
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
        }
        resp = requests.get(url, headers=headers)
        return resp
    except:
        return None


def get_chunk_list(length: int, chunk: int = 100) -> list:
    ''' 
    given a range and a chunk number,
    return a list of tuples containing start and end pos according to chunk size
    '''
    ret_list = []
    offset = 0
    for i in range(length):
        if (i+1)%chunk == 0:
            ret_list.append((offset, i))
            offset = i+1
    ret_list.append((offset, length-1))
    return ret_list


def update_scores_table_from_npm_search_criteria(conn: sqlite3.Connection) -> int:
    npm_registry_api = 'http://registry.npmjs.org/-/v1/search?text={name}'
    dncur = conn.cursor()
    dncur.execute(''' SELECT name FROM packages; ''')
    name_list = [x[0] for x in dncur.fetchall()]
    count = 0
    for index, pname in enumerate(name_list):
        response = get_api_data(npm_registry_api.format(name=pname))
        scores = [None, None, None, None] # final, popularity,quality, maintenance
        if response and response.status_code == 200:
            data = response.json()
            if is_valid_key(data=data, key='objects'):
                objects = data['objects']
                if len(objects) > 0:
                    pdata = objects[0]
                    if is_valid_key(data=pdata, key='package'):
                        package = pdata['package']
                        if package['name'] == pname or \
                            (is_valid_key(package, 'keywords') and pname in package['keywords']):
                            if is_valid_key(package, 'score'):
                                score = package['score']
                                count += 1
                                if is_valid_key(score, 'final'):
                                    scores[0] = score['final']
                                if is_valid_key(score, 'detail'):
                                    detail = score['detail']
                                    scores[1] = detail['popularity'] if is_valid_key(detail, 'popularity') else None
                                    scores[2] = detail['quality'] if is_valid_key(detail, 'quality') else None
                                    scores[3] = detail['maintenance'] if is_valid_key(detail, 'maintenance') else None
        dncur.execute(''' INSERT INTO scores VALUES (?, ?, ?, ?, ?); ''', [pname] + scores)
        print("updating npm search criteria scores on NPM packages [{}/{}]".format(index+1, len(name_list)), end='\r')
    print()
    return count


def update_scores_table_from_npmsio(conn: sqlite3.Connection) -> int:
    '''
    scores table stores the npms.io score system downloaded from npms.io public API
    score systems contains 4 metrics: final, popularity, quality, maintenance
    '''
    npms_io_api_mget = 'https://api.npms.io/v2/package/mget'
    dncur = conn.cursor()
    dncur.execute(''' SELECT name FROM packages; ''')
    name_list = [x[0] for x in dncur.fetchall()]
    pos_list = get_chunk_list(length=len(name_list), chunk=200)
    count = 0
    num_valid = 0
    while len(pos_list) > 0:
        temp_list = [] # temporary list for holding pos tuples having error code
        for (start_pos, end_pos) in pos_list:
            post_params = str(name_list[start_pos:end_pos+1]).replace('\'', '\"')
            response = post_api_data(url=npms_io_api_mget, data=post_params)
            if response.status_code != 200 and end_pos > start_pos:
                split_mid = int((end_pos-start_pos)/2)
                temp_list.append((start_pos, start_pos+split_mid))
                temp_list.append((start_pos+split_mid+1, end_pos))
            else:
                data = response.json()
                for name in name_list[start_pos:end_pos+1]:
                    count += 1
                    print('updating npms.io scores on NPM packages [{ind}/{total}]'.format(ind=count, total=len(name_list)), end='\r')
                    if is_valid_key(data=data, key=name):
                        p_data = data[name]
                        # name, final, popularity, quality, maintenance
                        values = [name, None, None, None, None]
                        if is_valid_key(data=p_data, key='score'):
                            score = p_data['score']
                            if is_valid_key(data=score, key='final'):
                                values[1] = float(score['final'])
                            if is_valid_key(data=score, key='detail'):
                                detail = score['detail']
                                if is_valid_key(data=detail, key='popularity'):
                                    values[2] = float(detail['popularity'])
                                if is_valid_key(data=detail, key='quality'):
                                    values[3] = float(detail['quality'])
                                if is_valid_key(data=detail, key='maintenance'):
                                    values[4] = float(detail['maintenance'])
                            # insert into database
                            try:
                                dncur.execute(''' INSERT INTO scores VALUES (?,?,?,?,?); ''', values)
                                num_valid += 1
                            except:
                                continue
        pos_list = temp_list
    print()
    return num_valid


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python3 preprocess.py <doc_file> <out_db_file>")
    
    raw_npm_doc = sys.argv[1] # raw npm data
    out_db = sys.argv[2] # ouput database
    dnconn = sqlite3.connect(out_db) # 'dep_network.db'

    # create tables: packages, depend, scores
    create_tables(dnconn)
    # updates packages table
    num_packages = update_packages_table(raw_npm_doc, dnconn)
    # update depend table
    num_depends = update_depend_table(dnconn)
    # update scores table
    # num_scores = update_scores_table_from_npmsio(dnconn)
    num_scores = update_scores_table_from_npm_search_criteria(dnconn)
    # print stats
    print('All updates finished')
    print('{} NPM packages, {} NPM dependency relationships, {} scores'
    .format(num_packages, num_depends, num_scores))
    dnconn.commit()
    dnconn.close()


if __name__ == '__main__':
    main()