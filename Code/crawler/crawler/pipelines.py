import json


class CrawlerPipeline(object):
    def open_spider(self, spider):
        self.file = open("../../Data/crawls/{}.json".format(spider.name), "w")

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        with open("../../Data/crawls/files/{}.html".format(item["node"]), "w+b") as f:
            f.write(item["html"])
        del item["html"]
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item
