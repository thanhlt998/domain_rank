import time


class TimeDownloaderMiddleware:
    def process_request(self, request, spider):
        request.meta['_start_time'] = time.time()

    def process_response(self, request, response, spider):
        request.meta['request_time'] = time.time() - request.meta['_start_time']
        return response

    def process_exception(self, request, exception, spider):
        pass
