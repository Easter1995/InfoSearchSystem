import scrapy
from IMDB.items import ImdbItem
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class ImdbspiderSpider(scrapy.Spider):
    name = "imdbSpider"
    allowed_domains = ["www.imdb.com"]
    cookies = {
        "session-id": "145-8250797-9764453",
        "ad-oo": "0",
        "ubid-main": "134-0217838-3023269",
        "ci": "eyJpc0dkcHIiOmZhbHNlfQ",
        "at-main": "Atza|IwEBINkpnrgJa-opAyB6fMXwUUe4Y3FwFC8rHG2ZtCv0njGX3gY2NESmes9bVlySvRWQL6pEygRKfQ_FTtRqfqtL7aAFVj8ASr7iEohsrvtl4ezMLZnCUYN_8fl6jn5azEaMKiLT5fJHI7yOS44YcwA8eNt0MV6ZAQwjnUUKlKl608uWB6JvGC7uqIaH_7YWWlMfxnzrcr-Chq9IAloyPZW7NqCIrt6Cm8JvjOfPSLcgyDms3A",
        "sess-at-main": "aceXcEcWz3XRsLImboJrb4RGEKe2SMLxOD6KnQGj/tg=",
        "uu": "eyJpZCI6InV1OTYwMTAxOWJjZmJmNDVlOGE1OTUiLCJwcmVmZXJlbmNlcyI6eyJmaW5kX2luY2x1ZGVfYWR1bHQiOmZhbHNlfSwidWMiOiJ1cjIwMTQ1NDQyNCJ9",
        "session-id-time": "2082787201l",
        "x-main": "ov9BTI1LFe2xQnBDN1AViIpOJJfE08I7IJ?66OJnOwl@IDmR9Ufc4EWtH1o2?@LF",
        "session-token": "nuMlpGueCL+mZprzHKotXMsaUr4hFON5ya0cQ2dRYr0+R/J167nJ17A/MRroDdbHD2GHij0BLrLMUK+gv1uUgh88GdCNHkn4IpTACfJgTluWxCxXv0jyFRyuIbF20Z6H0OWelf62EbiOLCSeMnsAw0TGe4wQVLp15dwr6E2wHy+dWna7s3HYor/+HjXNCvLtDsV3mIBxLrt4SmfVOHSV9IaShuBLzknRVPccmK08WVcj+5IDezENz6LTdvqtg4+gotBkwecNzcdVEbqr8eaLTdPo5SXaYI61hw6vGKhoLRkgglXcsuJRovDOdpx3r/pfvDXnnuMdtlXOIaJcWaYOq8fC5oXx1940zdGS7ZKM8btSiqyb+At3cLlAPkc83QdN",
        "csm-hit": "tb:s-1TYPTAXS3S7P3P0XZD07|1747376144181&t:1747376144181&adb:adblk_no"
    }

    def start_requests(self):
        yield SeleniumRequest(url='https://www.imdb.com/chart/top/?ref_=nv_mv_250', callback=self.parse, cookies=self.cookies)

    def parse(self, response):
        li_list = response.xpath('//*[@id="__next"]/main/div/div[3]/section/div/div[2]/div/ul/li')
        self.logger.info("Found %d movie rows", len(li_list))
        for item in li_list:
            page_url = item.xpath('./div/div/div/div/div[2]/div[1]/a/@href').get()
            detail_url = response.urljoin(page_url)
            yield SeleniumRequest(
                url=detail_url, 
                callback=self.parse_movie,
                wait_time=3,
                wait_until=EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    'div[data-testid="storyline-header"]'
                )),
                cookies=self.cookies,
                meta={'url': detail_url},
                script="""
                    // 先滚到 Storyline 标题
                    document.querySelector('div[data-testid="storyline-header"]')
                            .scrollIntoView({behavior:'instant',block:'center'});
                    // 再等待剧情摘要出现在 DOM
                    return new Promise(resolve => {
                    const check = () => {
                        if (document.querySelector('div[data-testid="storyline-plot-summary"]')) {
                            resolve();
                        } else {
                            setTimeout(check, 100);
                        }
                    };
                        check();
                    });
                """
            )

    def parse_movie(self, response):
        title = response.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[2]/div[1]/h1/span/text()').get()
        rate = response.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[3]/div[2]/div[2]/div[1]/div/div[1]/a/span/div/div[2]/div[1]/span[1]/text()').get()
        raw = response.xpath(
            "//div[@data-testid='storyline-plot-summary']"
            "//div[contains(@class,'ipc-html-content-inner-div')]/text()"
        ).get()
        summary = raw.strip() if raw else ""
        director = response.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[3]/div[2]/div[2]/div[2]/ul/li[1]/div/ul/li/a/text()').get()
        writers_list = response.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[3]/div[2]/div[2]/div[2]/ul/li[2]/div/ul/li')
        writers_arr = []
        for writer in writers_list:
            writers_arr.append(writer.xpath('./a/text()').get())
        writers = '/'.join(writers_arr)
        stars_list = response.xpath('//*[@id="__next"]/main/div/section[1]/section/div[3]/section/section/div[3]/div[2]/div[2]/div[2]/ul/li[3]/div/ul/li')
        stars_arr = []
        for star in stars_list:
            stars_arr.append(star.xpath('./a/text()').get())
        stars = '/'.join(stars_arr)
        url = response.meta['url']
        
        movie = ImdbItem()
        movie['title'] = title
        movie['rate'] = rate
        movie['summary'] = summary
        movie['director'] = director
        movie['writers'] = writers
        movie['stars'] = stars
        movie['url'] = url

        yield movie