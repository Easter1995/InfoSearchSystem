# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ImdbPipeline:
    i = 1
    def process_item(self, item, spider):
        dict_item = dict(item)
        with open('source/' + str(self.i) + '.txt', 'w', encoding='utf-8') as file:
            file.write(dict_item['title'] + '\n')
            file.write('rate: ' + dict_item['rate'] + '\n')
            file.write('director: ' + dict_item['director'] + '\n')
            file.write('writers: ' + dict_item['writers'] + '\n')
            file.write('stars: ' + dict_item['stars'] + '\n')
            file.write(dict_item['summary'] + '\n')
            file.write('url: ' + dict_item['url'] + '\n')
        
        self.i += 1
        
        return item
