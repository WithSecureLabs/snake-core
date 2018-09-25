# pylint: disable=missing-docstring

from os import path

from urllib import parse
import cgi
import requests

from snake import config
from snake import error
from snake import fields
from snake import scale

PROXIES = {}
if config.snake_config['http_proxy']:
    PROXIES['http'] = config.snake_config['http_proxy']
if config.snake_config['https_proxy']:
    PROXIES['https'] = config.snake_config['https_proxy']

HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": config.constants.USER_AGENT
}


class Upload(scale.Upload):
    def arguments(self):
        return {
            'url': fields.Str(required=True)
        }

    def info(self):
        return "fetches files from arbitrary URLs and uploads them to Snake"

    def upload(self, args, working_dir):
        url_parser = parse.urlparse(args['url'])
        if not url_parser.scheme:
            url_parser = parse.urlparse('http://' + args['url'])
        req = requests.get(url_parser.geturl(),
                           headers=HEADERS,
                           proxies=PROXIES,
                           stream=True,
                           timeout=300)
        if not req.status_code == requests.codes.ok:  # pylint: disable=no-member
            raise error.UploadError('HTTP Error: %s - %s' % (req.status_code, req.reason))

        name = None
        if 'Content-Disposition' in req.headers:
            _, params = cgi.parse_header(req.headers['Content-Disposition'])
            if 'filename' in params:
                name = params['filename']
        if not name:
            name = args['url'].split('/')[-1]
        with open(path.join(working_dir, name), 'wb') as f:
            for chunk in req.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
        return name
