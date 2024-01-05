import requests
import re
from parsel import Selector
import json

existing_profile_urls = set()

def regex_parse(pattern,text):
    # For Parsing Regex statement
    if re.search(pattern,str(text),re.I):
        data = re.findall(pattern,str(text),re.I)[0]
        return data
    else:
        return ''

def main_publisher_listing_page(listing_page_url,session,payload,headers):
    # Going for magazine listing requests
    listing_page_response = session.post(url=listing_page_url,headers=headers,data=payload)
    if listing_page_response.status_code == 200:
        item = {}
        listing_json_data = json.loads(listing_page_response.text)
        main_lt = []
        for block in listing_json_data[:3]:
            main_item = {}
            url = f'https://kendam.com/{block.get("url","")}'
            # Check with exsisting data link
            if url not in existing_profile_urls:
                existing_profile_urls.add(url)
                listing_main_response = session.get(url)
                listing_res = Selector(text=listing_main_response.text)
                akey = regex_parse(r'akey\s*\=\s*\"(.*?)\"',listing_main_response.text)
                post_url = 'https://kendam.com/api/v8/page/news/'
                url_part = regex_parse(r'var\s*url\s*\=\s*\"(.*?)\"',listing_main_response.text)
                main_item["url"] = listing_res.xpath('//i[@class="icon-link"]/following-sibling::a/@href').get('').strip()
                main_item["new_page"] = True
                main_item["type"] = block.get('atype','')
                main_item["name"] = block.get('name','')
                main_item["address"] = (regex_parse(r'icon\-location\"><\/i>(.*?)<\/p>',listing_main_response.text)).strip()
                main_item["logo"] = block.get('avi','')
                main_item["instagram"] = listing_res.xpath('//i[@class="icon-instagram"]/parent::a/@href').get('').strip()
                main_item["facebook"] = listing_res.xpath('//i[@class="icon-facebook"]/parent::a/@href').get('').strip()
                main_item["twitter"] = listing_res.xpath('//i[@class="icon-twitter"]/parent::a/@href').get('').strip()
                main_item["source_url"] = url
                description = regex_parse(r'<h3>About<\/h3><p>(.*?)<\/p>',listing_main_response.text)
                if description:
                    main_item['description'] = description
                else:
                    main_item['description'] = 'null'
                headers['referer'] = url
                collection_lt = []
                pagination_check = listing_res.xpath('//div[@id="more-news-latest"]/text()').get('').strip()
                payload = ''
                if pagination_check:
                    for page in range(0,1):
                        offset_val = page*10
                        payload = f"akey={akey}&url={url_part}&order=recent&offset={offset_val}"
                else:
                    payload = f"akey={akey}&url={url_part}&order=recent&offset=0"
                listing_json_response = session.post(url=post_url,headers=headers,data=payload)
                listing_data = json.loads(listing_json_response.text)
                for list_block in listing_data:
                    collection_item = {}
                    title = list_block.get('title_full','')
                    collection_item["name"] = title
                    intro_dump = list_block.get('intro','')
                    photographer = (regex_parse(r'\,(.*?)\s*\(Photographer\)',intro_dump)).strip()
                    if photographer:
                        collection_item["Photographer"] = photographer
                    else:
                        collection_item["Photographer"] = 'null'
                    model = (regex_parse(r'with(.*?)\s*\(Model\)',intro_dump)).strip()
                    if model:
                        collection_item["Model"] = model
                    else:
                        collection_item["Model"] = 'null'
                    mag_link = list_block.get('link','')
                    mag_response = session.get(mag_link)
                    mag_sel = Selector(text=mag_response.text)
                    date = mag_sel.xpath('//div[@class="headers header-period"]/text()').get('').strip()
                    collection_item["date"] = date
                    collection_item["season"] = 'null'
                    collection_item["year"] = (date.split(',')[-1]).strip()
                    collection_item["type"] = list_block.get('category_name','')
                    if re.search(r'men|man',title,re.I):
                        collection_item["gender"] = 'male'
                    elif re.search(r'men',title,re.I) and re.search(r'wmn|women',title,re.I):
                        collection_item["gender"] = 'both'
                    else:
                        collection_item["gender"] = 'women'
                    
                    image_lt_var = [] 
                    ima_dict = {}
                    first_im = mag_sel.xpath('//img[@class="full main-picture"]/@src').get('').strip()
                    image_link = mag_sel.xpath('//a[@class="aap-link"]/@href').get('').strip()
                    image_check = regex_parse(r'<h5>\+(.*?)<\/h5>',mag_response.text)
                    ima_dict["url"] = first_im
                    ima_dict["display_order"] = '1'
                    image_lt_var.append(ima_dict)
                    image_sh = image_link.split('/')[-1]
                    image_response = session.get(image_link)
                    akey = regex_parse(r'akey\s*\=\s*\"(.*?)\"',image_response.text)
                    headers['referer'] = image_link
                    image_url = 'https://kendam.com/api/v8/photos/album/'
                    image_lt = [] 
                    limit = 0
                    if image_check != '':
                        page_limit = int(image_check)//9
                        for page_off in range(0,page_limit+1): 
                            off_set_page = page_off*9
                            payload = f"akey={akey}&shortlink={image_sh}&offset={off_set_page}&token="
                            image_p_response = session.post(image_url,headers=headers,data=payload)
                            if image_p_response.text != 'empty':
                                json_im = json.loads(image_p_response.text)
                                for count,im_block in enumerate(json_im,1):
                                    if limit > 0:
                                        count = (page_off*10) + count -1
                                    else:
                                        count = count
                                    im_p = {}
                                    im_p["url"] = im_block.get('full_img','')
                                    im_p["display_order"] = f'{count}'
                                    image_lt.append(im_p)
                                limit += 1
                                collection_item["images"] = image_lt
                                collection_lt.append(collection_item)
                            else:
                                collection_item["images"] = image_lt_var
                                collection_lt.append(collection_item)
                                break
                main_item["collection"] = collection_lt                        
                main_lt.append(main_item)
    
        item["page"] = main_lt
        return item
    

if __name__ == '__main__':
    url = 'https://kendam.com/pages/publishers/'
    session = requests.Session()
    main_response = session.get(url)  
    listing_page_url = 'https://kendam.com/api/v9/pages/show/'
    # Initially set the offset for one page only
    payload = "offset=0&category=publishers"
    headers = {
        'Accept': 'text/html, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://kendam.com',
        'Referer': 'https://kendam.com/pages/publishers/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    # Going to function to scrape
    item = main_publisher_listing_page(listing_page_url,session,payload,headers)
    # Writing the Scraped Data into JSON
    with open('task_2_publisher_sample_v1.json','w') as json_file:
        json.dump(item,json_file,indent=2,ensure_ascii=False)