from scrapy.exporters import JsonItemExporter
import os


class JsonPipeline(object):
    def open_spider(self, spider):
        if not os.path.exists("data"):
            os.makedirs("data")
        self.file = open("data/" + spider.name + ".json", "wb")
        self.exporter = JsonItemExporter(
            self.file, encoding="utf-8", ensure_ascii=False
        )
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
