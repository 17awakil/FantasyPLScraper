import requests
from bs4 import BeautifulSoup
import re
# import backoff

def get_table(url, table_no=0):
    res = requests.get(url)
    ## The next two lines get around the issue with comments breaking the parsing.
    comm = re.compile("<!--|-->")
    soup = BeautifulSoup(comm.sub("",res.text),'lxml')
    all_tables = soup.findAll("tbody")    
    table = all_tables[table_no]
    return table

""" Parse a table in HTML and returns a table as a list of dictionaries"""
def get_stats(table):
    stats = []
    for row in table.contents:
        if row.name == "tr" and not row.has_attr("class"):
            rowStats = {}
            for col in row.contents:
                if col.name == "td":
                    rowStats[col.attrs["data-stat"]] = col.text
            stats.append(rowStats)
    return stats

        
table = get_table("https://fbref.com/en/comps/9/stats/Premier-League-Stats",table_no=2)
get_stats(table)