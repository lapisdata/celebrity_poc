import re
import json
import requests
from parsel import Selector
from datetime import datetime


def parse(response):

    # Request popular celebrities page
    popular_url = 'https://celebmafia.com/popular-celebrities/'
    popular_response = requests.get(popular_url)
    popular_response_1 = Selector(popular_response.text)
    
    popular_links = popular_response_1.xpath('//div[@id="mcTagMap"]//ul/li/a/@href').getall()
    
    celebrity_output = []
    celeberities_response = Selector(response.text)
    celeberities_links = celeberities_response.xpath('//div[@id="mcTagMap"]//ul/li/a')

    # Set to keep track of existing profile URLs
    existing_profile_urls = set()
    
    # Loop through 100 celebrity links
    for celebrity_url in celeberities_links[0:100]:
        celebrity_url = celebrity_url.xpath('./@href').get('')

        # Check if the profile URL is not in the set
        if celebrity_url not in existing_profile_urls:
            new_profile = True
            celebrity_response=celebrity_parsing(celebrity_url, new_profile, popular_links)
            celebrity_output.append(celebrity_response)
            # Add the URL to the set
            existing_profile_urls.add(celebrity_url)
            
            
        else:
            new_profile = False
            celebrity_parsing(celebrity_url, new_profile, popular_links)
            print(f"The link {celebrity_url} is already present in the list.")
            
    # Convert the scraped data to JSON format
    celebrity_json_data = json.dumps(celebrity_output, indent=2, ensure_ascii=False)
    
    
    # Save JSON data to a file
    with open('Celebritymafia_output.json', 'w', encoding='utf-8-sig') as json_file:json_file.write(celebrity_json_data)

def celebrity_parsing(celebrity_url, new_profile, popular_links):
    
    # Check if it's a new profile
    if new_profile:
        
        # Request celebrity page
        celebrity_response = requests.get(celebrity_url)
        celebrity_response_1 = Selector(celebrity_response.text)

        # Dictionary to store profile information
        item = {
            'profile': celebrity_response_1.xpath('//h1[@class="archive-title"]/text()').get(''),
            'profile_url': celebrity_url,
            'new_profile': new_profile,
            'popular': celebrity_url in popular_links,
            'collections': []
        }

        # Extract information about collections
        profile_links = celebrity_response_1.xpath('//a[@class="entry-title-link"]/@href').getall()
        for profile_link in profile_links:
            profile_response = requests.get(profile_link)
            profile_response_1 = Selector(profile_response.text)

            collection_name = profile_response_1.xpath('//h1[@class="entry-title"]/text()').get('')
            if collection_name:
                collection_name = collection_name.split('–')[-1].strip()
                collection_date = collection_name.split(' ')[-1]
                if re.search(r'\d{2}/\d{2}/\d{4}',collection_date):
                    date = collection_date
                else:
                    date = profile_response_1.xpath('//time[@class="entry-time"]/text()').get(' ')
                    parsed_date = datetime.strptime(date, '%B %d, %Y')

                    # Format the date in MM/DD/YYYY format
                    date = parsed_date.strftime('%m/%d/%Y')
                images=profile_response_1.xpath('//div[@class="entry-content"]//div/a/img/@src').getall()
                
                profile = {
                    'name': ' '.join(collection_name.split(' ')[0:-1]),
                    'date': date,
                    'categories': profile_response_1.xpath('//a[@rel="category tag"]/text()').get(''),
                    'images': images
                }
                item['collections'].append(profile)
        return item
        
        
    


if __name__ == '__main__':
    url = 'https://celebmafia.com/list-of-celebrities/'
    response = requests.get(url)
    # Call the parsing function with the main page response
    parse(response)
