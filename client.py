import os
import time
import pickle
import json
import asyncio

from typing import Any
from enum import Enum

import httpx


class Errors(Enum):
    UNKNOWN_ERROR = 1
    WRONG_TOKEN = 2
    RATE_LIMIT = 3
    EMPTY_TOKEN = 4
    NOT_LOGGED_IN = 5
    ALREADY_LOGGED_IN = 6
    SEND_CODE_FIRST = 7



class Tag: # TODO
    def __init__(self,text:str, flipped:bool,icon_color:str,icon_url:str) -> None:
        self.text = text
        self.flipped = flipped
        self.icon_color = icon_color
        self.icon_url = icon_url
    
    @classmethod
    def from_dic(cls,dict):
        return cls(dict.get("text"),dict.get("flipped"),dict.get("icon_color"),dict.get("icon_url"))
        
    def __str__(self):
        if any((self.text,self.flipped,self.icon_color,self.icon_url)):
            return f"{self.__class__.__name__}(text={self.text}, flipped={self.flipped}, icon_color={self.icon_color}, " \
               f"icon_url={self.icon_url})"
        else:
            return '(Empty)'
class Badge: # TODO
    pass


class Item: # TODO
    def __init__(self, key_prop_name, badge, bottom_description, has_chat, images, middle_description, padded, red_text,tag,
                 title, token, top_description, widget_type, type, link,):
        self.key_prop_name = key_prop_name
        self.badge = badge
        self.bottom_description = bottom_description
        self.has_chat = has_chat
        self.images = images
        self.middle_description = middle_description
        self.padded = padded
        self.red_text = red_text
        self.tag = tag
        self.title = title
        self.token = token
        self.top_description = top_description
        self.widget_type = widget_type
        self.type = type
        self.link = link

        
        

    @classmethod
    def from_dict(cls,dict):
        ttype = dict.get("type")
        dict = dict.get("data")
        return cls(dict.get("KEY_PROP_NAME"),Badge(),dict.get("bottomDescription"),dict.get("hasChat"),dict.get("image"),\
                   dict.get("middleDescription"),dict.get("padded"),dict.get("redText"),Tag.from_dic(dict.get('tag',{})),dict.get("title"),\
                    dict.get("token"),dict.get("topDescription"),dict.get("widgetType"),ttype,"https://divar.ir"+dict['action']['props']['to'] if dict.get("action") else "")
    
    def __str__(self):
        return f"{self.__class__.__name__}: key_prop_name='{self.key_prop_name}', badge='{self.badge}', bottom_description='{self.bottom_description}', " \
               f"has_chat={self.has_chat}, images={self.images}, middle_description={self.middle_description}, " \
               f"padded={self.padded}, red_text='{self.red_text}', tag={self.tag}, title='{self.title}', token='{self.token}', " \
               f"top_description={self.top_description}, widget_type={self.widget_type}, type={self.type}, link='{self.link}'\n"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: key_prop_name='{self.key_prop_name}', badge='{self.badge}', bottom_description='{self.bottom_description}', " \
               f"has_chat={self.has_chat}, images={self.images}, middle_description={self.middle_description}, " \
               f"padded={self.padded}, red_text='{self.red_text}', tag={self.tag}, title='{self.title}', token='{self._token}', " \
               f"top_description={self.top_description}, widget_type={self.widget_type}, type={self.type}, link='{self.link}'\n"

class DivarClient:
    #TODO Add a function to scrap full details of one post
    def __init__(self) -> None:
        self.session = httpx.AsyncClient(follow_redirects=True)
        self._code_reqeust = None
        self._token = None

        self.init_headers()

    def init_headers(self):
        headers = {
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203",
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US,en;q=0.9',
            'Cache-Control':'max-age=0',
        }
        self.session.headers = headers
    
    async def parse_page(self,resp:httpx.Response)->dict:
        async for line in resp.aiter_lines():
            if 'window.__PRELOADED_STATE__' in line:
                line = line.replace("window.__PRELOADED_STATE__ =","").replace(";","")
                return json.loads(line)
    
    async def get_city_items(self,response:dict)->map:
        return map(lambda x:Item.from_dict(x),response['browse']['items'])
    
    
    async def scrap_city(self,city,page=1,category="ROOT",search=None,has_photo=None,urgent=None,price_from=None,price_to=None)->tuple[list[Item]]:
        #TODO Make this function an async generator
        base = f"https://divar.ir/s/{city}/"
        params = {}
        if category != "ROOT":
            base += category
        if search is not None:
            params['q'] = search
        if has_photo == True:
            params['has_photo'] = True
        price_from = price_from or ""
        price_to = price_to or ""
        price_range = f"{price_from}-{price_to}"
        if price_range != "-":
            params['price'] = price_range
        if urgent:
            params['urgent'] = True

        resp = await self.session.get(base,params=params)
        parsed_dict = await self.parse_page(resp)
        items = tuple(await self.get_city_items(parsed_dict))
        pages_data = [items]

        if page>1:
            current_page = 1
            last_post_date = parsed_dict['browse']['lastPostDate']
            city_id = parsed_dict['city']['city']['id']
            while current_page<page:
                page_posts = []
                data = {
                    "page": current_page,
                    "json_schema": {
                        "category": {
                            "value": category
                        },
                        "cities": [
                            str(city_id)
                        ]
                    },
                    "last-post-date": int(last_post_date)
                }

                resp = await self.session.post(f"https://api.divar.ir/v8/web-search/{city_id}/{category}",json=data)
                json_resp = resp.json()
                last_post_date = json_resp['last_post_date']
                next_page = json_resp['seo_details']['next'] # TODO check if next page exists
                posts = json_resp['web_widgets']['post_list']
                for post in posts:
                    pd = post['data']
                    try:
                        pt = pd['action'].get("type")
                        if pt == "VIEW_POST":
                            web_info = pd['action']['payload']['web_info']
                            title = web_info['title'].replace(" ","-")
                            slug = web_info['category_slug_persian'].replace(" ","-")
                            city = web_info['city_persian'].replace(" ","-")
                            link = "/v/"+f"{title}_{slug}_{city}__دیوار" + f"/{pd['token']}"
                        elif pt =='SERVICES_VIEW_PROFILE':
                            link = "/services/"+pd['action']['payload']['cat']+'/'+ pd['action']['payload']['slug']
                        else:
                            print("[!] Unknown pt type:",pt)
                        data = {
                            "data":{
                                "KEY_PROP_NAME":"",
                                "bottomDescription":pd['bottom_description_text'],
                                "hasChat":pd['has_chat'],
                                "image":pd['image_url'],
                                "middleDescription":pd['middle_description_text'],
                                "padded":pd['padded'],
                                "redText":pd['red_text'],
                                "tag":{},
                                "title":pd['title'],
                                "token":pd['token'],
                                "topDescription":pd['top_description_text'],
                                "widgetType":post['widget_type'],
                                "action":{
                                    "props":{
                                        "to":link
                                    }
                                }
                            },
                            "type":""
                        }
                        page_posts.append(Item.from_dict(data))
                    except Exception as ex:
                        pass
                pages_data.append(tuple(page_posts))
                current_page+=1
                await asyncio.sleep(1)

            
        return tuple(pages_data)


    async def login(self,phone:str) -> Errors | Any:
        if os.path.exists(f"{phone.strip()}-token.txt"):
            self._token = open(f"{phone}-token.txt").read()
            self.session.cookies = httpx.Cookies(pickle.load(open(f"{phone}-cookies","rb")))
            self.session.cookies['token'] = self._token
            return True
        else:
            return Errors.NOT_LOGGED_IN
        

    async def send_code(self,phone:str):
        data ={
            "phone":phone
        }
        resp = await self.session.post("https://api.divar.ir/v5/auth/authenticate",json=data)       
        rj = resp.json()
        if rj.get("authenticate_response") == "AUTHENTICATION_VERIFICATION_CODE_SENT":
            self._code_reqeust = int(time.time())
            return True

    async def enter_code(self,phone:str, code:str):
        if not self._code_reqeust or time.time() - self._code_reqeust > 120: 
            return Errors.SEND_CODE_FIRST
        data = {
            "phone":phone,
            "code":code.strip(),
        }
        resp = await self.session.post("https://api.divar.ir/v5/auth/confirm",json=data)
        json_resp = resp.json()
        if json_resp.get("token"):
            open(f"{phone}-token.txt","w").write(json_resp['token'])
            pickle.dump(dict(self.session.cookies),open(f"{phone}-cookies","wb"))
            return True
        else:#TODO
            pass
    
    async def check_unread(self):
        if not self._token:
            return Errors.NOT_LOGGED_IN
        data = {
            "token":self._token
        }
        resp = await self.session.post("https://chat.divar.ir/api/unread",json=data)
        return resp.json().get("unread")

    async def get_phone_number(self,token:str,is_service:bool=False)->Errors | Any:
        if os.path.exists("phone-limit.txt"):
            limit = open("phone-limit.txt").read()
            if time.time() - float(limit) <2*60*60: # Check Again every 2 hours
                return Errors.RATE_LIMIT
                
        if not self._token:
            return Errors.NOT_LOGGED_IN
        if not token:
            return  Errors.EMPTY_TOKEN
        if is_service:
            resp = await self.session.get(f"https://api.divar.ir/v8/postcontact/web/contact_info/services_profile_{token}")
            j_resp = resp.json()
        else:
            resp = await self.session.get(f"https://api.divar.ir/v8/postcontact/web/contact_info/{token}")
            j_resp = resp.json()
            if j_resp.get("code")== 5:
                return await self.get_phone_number(token,True)
        if wl:=j_resp.get("widget_list"):
            if wl[0]['data']['action']['type'] == 'CALL_SUPPORT':
                return wl[0]['data']['value']
            else:
                return "PHONE_IS_HIDE"
        elif j_resp['code'] == 2:
            return Errors.WRONG_TOKEN
        elif j_resp['code'] == 8:
            open("phone-limit.txt","w").write(str(time.time()))
            return Errors.RATE_LIMIT
        

  

                



            
async def benchamrk():
    cli = DivarClient()
    tasks = [cli.scrap_city("tehran",2), cli.scrap_city("bushehr",2), cli.scrap_city("zanjan",2),cli.scrap_city("shiraz",2)]
    before = time.time()
    results = await asyncio.gather(*tasks)
    after = time.time()
    page_count = 0
    item_count = 0
    for city in results:
        for page in city:
            page_count+=1
            for _ in page:
                item_count +=1
    print(f"[+] Scrap {len(tasks)} city {page_count} page and {item_count} item in '{after-before:0.4f}' seconds")
        
    


async def main():
    await benchamrk()
    



asyncio.run(main())

