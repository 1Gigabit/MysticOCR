class BulkDataObj:
    def __init__(self, data):
        self.object = data.get('object')
        self.id = data.get('id')
        self.type = data.get('type')
        self.updated_at = data.get('updated_at')
        self.uri = data.get('uri')
        self.name = data.get('name')
        self.description = data.get('description')
        self.size = data.get('size')
        self.download_uri = data.get('download_uri')
        self.content_type = data.get('content_type')
        self.content_encoding = data.get('content_encoding')


class BulkData:
    def __init__(self, json_data):
        self.object = json_data.get('object')
        self.has_more = json_data.get('has_more')
        self.data = [BulkDataObj(data) for data in json_data.get('data')]
