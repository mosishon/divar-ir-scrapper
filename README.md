# divar-ir-scrapper
## نصب :
1 - `git clone https://github.com/mosishon/divar-ir-scrapper.git`</br>
2 - `cd divar-ir-scrapper`</br>
3 - `pip install -r requirements.txt`</br>

## استفاده:
### ساخت کلاینت:
`cli = DivarClient()`
### اسکرپ کردن صفحه اصلی یک شهر
`cli.scrap_city("tehran")`
### افزایش تعداد صفحات
`cli.scrap_city("tehran",page=2)`
### اسکرپ کردن صفحه اصلی یک دسته بندی خاص
`cli.scrap_city("tehran",page=2,category='vehicles')`
### سرچ کردن 
`cli.scrap_city("tehran",search='موتور')`

### فعال کردن فیلتر فقط عکس دار 
`cli.scrap_city("tehran",has_photo=True)`
### فعال کردن فیلتر فقط فوری
`cli.scrap_city("tehran",urgent=True)`
### فعال کردن رنج قیمتی

حداقل قیمت از ۱۰۰۰ : `cli.scrap_city("tehran", price_from=1_000)` </br>
حداکثر قیمت تا ۱۰۰۰۰ : `cli.scrap_city("tehran", price_to=10_000)`</br>
قیمت از ۱۰۰۰ تا ۱۰۰۰۰ : `cli.scrap_city("tehran", price_from=1_000, price_to=10_000)`</br>

## نمونه کد کامل
```
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


# Scrap 4 city 8 page and 192 item in '5.0332' seconds

```
