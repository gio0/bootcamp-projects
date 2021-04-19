from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import time
import os.path
import pandas as pd
from tqdm import tqdm


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns true if the response seems to be HTML, false otherwise
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)
    

# Scraping
f = 'data/cycle-soup.csv'

if os.path.exists(f):
    df = pd.read_csv(f, header=None)
    lower_bound = df.iloc[:,5].max() + 1
else:
    lower_bound = 1
    

pages = 1111
url_base = 'https://www.cyclesoup.com/srp?page='

for page in tqdm(range(lower_bound, pages + 1)):
    # for response delay
    t0 = time.time()
    
    html = simple_get(f'{url_base}{page}')
    soup=BeautifulSoup(html,'html.parser')
    
    articles = soup.find_all('article')
    
    lst = []
    for article in articles:
    
        data_list = article.find('dl')
        data_headers = [i.text.strip() for i in data_list.find_all('dt')]
        data_values  = [i.text.strip() for i in data_list.find_all('dd')]
        
        bike_info               = dict(zip(data_headers, data_values))
        bike_info['page']       = page
        bike_info['lat']        = article.find(class_="location-mi").get('lat')
        bike_info['lon']        = article.find(class_="location-mi").get('long')
        bike_info['year_brand'] = article.find(class_="h6").next_element
        bike_info['model']      = article.find('span', {'class': 'article-subtitle'}).text
        bike_info['price']      = article.find(class_="vehicle-price").text
        bike_info['id']         = article.find('a', {'class':'btn'}).get('href')
        
        lst.append(bike_info)

    # response delay
    response_delay = time.time() - t0
    time.sleep(1.1*response_delay)

    bike_df = pd.DataFrame(lst)
    bike_df.to_csv(f, mode='a', header=False, index=False)
    
    
# add header
names = list(lst[0].keys())
df = pd.read_csv(f, names=names)
df.to_csv(f, index=False)