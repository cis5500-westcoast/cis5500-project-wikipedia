import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import csv
import threading
import queue
import codecs
import pandas as pd

# Function to write the data to a csv file
def write_csv(results):
    df = pd.DataFrame(results, columns=['Original Name', 'Player', 'Wikipedia', 'Image URL'])
    #df = df.concat(results)
    df.to_csv('player_wikipedia.csv', index=False, header=True)
    with pd.ExcelWriter('player_wikipedia.xlsx', engine='xlsxwriter', options={'encoding': 'utf-8'}) as writer:
        df.to_excel(writer, index=False)
    # Define the encoding to use
    #encoding = 'utf-8'
    #with codecs.open('player_wikipedia.csv', 'w', encoding=encoding) as csvfile:
    #writer = csv.writer(csvfile)
    #writer.writerow(['Original Name', 'Player', 'Wikipedia', 'Image URL'])

    #for i in range(len(results)):
    #    writer.writerow(results[i])

def worker(row, queue):
    player = urllib.parse.quote(row[0])
    url = 'https://en.wikipedia.org/w/api.php?action=opensearch&search=' + player + '&format=json&origin=*'
    #print(url)
    search_response = requests.get(url)
    data = search_response.json()

    # Find the URL in the JSON object
    #print(data)
    for each in data:
        for string in each:
            if "https" in string:
                #print(string)
                # Get wikepidia page
                req = Request(string, headers={'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                soup = BeautifulSoup(webpage, 'html.parser')

                # Check and see if soccer page
                check_url = '/wiki/Association_football'
                # 1) Find all links in the page
                links = soup.find_all('a')

                # 2) Check if the target URL is present in any of the links
                url_exists = False
                for link in links:
                    #print(link)
                    if link.get('href') == check_url:
                        url_exists = True
                        break
                
                # 3) Check_url exists, capture data
                if url_exists:

                    # Get the updated URL
                    # Find the link element with the specified rel attribute
                    canonical_element = soup.find('link', {'rel': 'canonical'})
                    if canonical_element is not None:
                        # Extract the href attribute value of the link element    
                        updated_url = canonical_element['href']
                    else:
                        # Code to execute if the link element is not found
                        updated_url = ""

                    # Get updated player name
                    span_element = soup.find('span', {'class': 'mw-page-title-main'})
                    if span_element is not None:
                        # Extract the text of the span element
                        player_name_text = span_element.text
                    else:
                        # Code to execute if the span element is not found
                        player_name_text = ""

                    # Get profile image
                    # 1) Find the link element containing the infobox image
                    link_element = soup.find('a', {'class': 'image'})
                    if link_element is not None:
                        # 2) Find the td element containing the infobox image
                        td_element = link_element.find_parent('td', {'class': 'infobox-image'})
                        if td_element is not None:
                            # 3) Find the img element containing the image URL
                            img_element = td_element.find('img')
                            if img_element is not None:
                                # 4) Extract the src attribute value of the img element
                                image_url = img_element['src']
                            else:
                                # Code to execute if the img_element is not found
                                image_url = ""
                        else:
                            # Code to execute if the td_element is not found
                            image_url = ""
                    else:
                        # Code to execute if the link_element is not found
                        image_url = ""
                    
                    # Add to lists
                    # Create a list of variables
                    utf8_string = urllib.parse.unquote(player)
                    #variable_list = [utf8_string + ", " + player_name_text + ", " + updated_url + ", https://" + image_url]
                    variable_list = [utf8_string, player_name_text, updated_url, image_url]

                    # Convert the list of variables to a string
                    #variable_string = ', '.join(str(variable) for variable in variable_list)

                    #print('original name: ', utf8_string, ' - player name: ', player_name_text, '- url: ', updated_url, '- image url: ', image_url)
                    queue.put(variable_list)


with open('player_names.csv', newline='') as csvfile:
    soccer_players = csv.reader(csvfile,  delimiter=',')

    queue = queue.Queue()
    results = []
    
    threads = []
    for row in soccer_players:
        # Create worker threads
        t = threading.Thread(target=worker, args=(row, queue))
        threads.append(t)
        t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Get results from the Queue
        while not queue.empty():
            result = queue.get()
            print(result)
            results.append(result)

    print(results)
    write_csv(results)
            
        