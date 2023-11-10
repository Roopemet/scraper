import pandas as pd
from scipy.stats import poisson
import requests
from bs4 import BeautifulSoup
import time

#get a list of matches to scrape
def get_matchlinks(url):
    
    lista = []
    r = requests.get(url)

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        link_sources = soup.find_all('td', {'class': 'center', 'data-stat': 'score'})
        
        for row in link_sources:
            link = row.find('a', href=True)
            if link:
                lista.append(link['href'])
                
    return lista

#gets match data from a link and returns them
def get_matchdata(linkki):
    r = requests.get(linkki)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        box = soup.find_all('div', {'class': 'scorebox_meta'})
        for row in box:
            link = row.find('a', href=True)
            if link:
                link = (link['href'])
                pvm = link.split('/')[-1]
                
    table = pd.read_html(linkki)
    home = table[2].columns[0][0]
    away = table[2].columns[1][0]

    home_poss = table[2].iat[0,0]
    away_poss = table[2].iat[0,1]
  
    for i in [3,4,10,11]:
        table[i].columns = table[i].columns.droplevel()
    
    lastrow_table3 = len(table[3].index)-1
    lastrow_table4 = len(table[4].index)-1
    lastrow_table10 = len(table[10].index)-1
    lastrow_table11 = len(table[11].index)-1

    home_goals = table[3].at[lastrow_table3,'Gls']
    away_goals = table[10].at[lastrow_table10,'Gls']

        
    home_xg = table[3].at[lastrow_table3,'xG']
    away_xg = table[10].at[lastrow_table10,'xG']

    home_cmplt = table[4].at[lastrow_table4,'Cmp%'][0]
    away_cmplt = table[11].at[lastrow_table11,'Cmp%'][0]

    return[pvm, home,away, home_goals, away_goals, home_poss, away_poss,
           home_xg,away_xg,home_cmplt,away_cmplt]

#gets match data for the whole season and forms a csv
def get_matches(season):
    url = 'https://fbref.com/en/comps/9/'+season +'/schedule/' + season+ '-Premier-League-Scores-and-Fixtures'
    
    match_links = get_matchlinks(url)
    season_stats = []
    
    for linkki in match_links:
        #sleep is necessary to not get timed out by the server
        time.sleep(5)
        urli = 'https://fbref.com' + linkki
        row = get_matchdata(urli)
        print(row)
        season_stats.append(row)
    
    headers = ['pvm', 'home', 'away', 'home_goals', 'away_goals',
               'home_poss','away_poss', 'home_xg', 'away_xg',
               'home_cmplt', 'away_cmplt']
    
    df = pd.DataFrame(season_stats, columns = headers)
    df['home_poss'] = df['home_poss'].str.rstrip('%').astype(float)/100
    df['away_poss'] = df['away_poss'].str.rstrip('%').astype(float)/100

    df.to_csv(season  + '.csv', encoding='utf-8')

seasons = ['2019-2020', '2020-2021', '2021-2022', '2022-2023']
dft=[]
for season in seasons:
    #get_matches(season)
    df = pd.read_csv(season + '.csv', index_col=0)
    dft.append(df)
    
#cleaning data
df_all = pd.concat(dft)
df_all['date'] = pd.to_datetime(df_all['date'])
df_all['home_goals'] = df_all['home_goals'].astype(int)
df_all['away_goals'] = df_all['away_goals'].astype(int)

#add column for goal and xg difference
df_all['goal_diff'] = df_all.home_goals - df_all.away_goals
df_all['xg_diff'] = df_all.home_xg - df_all.away_xg

#group home advantage for every team
df_homeadv = (df_all.groupby("home")['xg_diff'].median() + 
              df_all.groupby("away")['xg_diff'].median())
              
#can conclude that home advantage is roughly +0,2 goals. Sample for specific teams is likely too small
print(f'mean xg difference: {df_all["xg_diff"].mean()}')
print(f'median xg difference: {df_all["xg_diff"].median()}')
print(f'median goal difference: {df_all["goal_diff"].mean()}')
print("Difference in Home vs Away XG per team:")
print(df_homeadv)







