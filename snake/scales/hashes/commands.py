# pylint: disable=missing-docstring
# pylint: disable=no-self-use
# pylint: disable=unused-argument

import hashlib
import logging
import shutil

from snake import db
from snake import enums
from snake import error
from snake import scale
from snake.utils import markdown as md


app_log = logging.getLogger("tornado.application")  # pylint: disable=invalid-name


try:
    import pydeep
    has_ssdeep = True  # pylint: disable=invalid-name
except ImportError as err:
    app_log.warning('fuzzy search disabled - optional dependencies not met: %s', err)
    has_ssdeep = False  # pylint: disable=invalid-name


class Commands(scale.Commands):
    def check(self):
        if has_ssdeep:
            ssdeep = shutil.which('ssdeep')
            if not ssdeep:
                app_log.warning('binary \'ssdeep\' not found')

    @scale.command({
        'info': 'list all calculated hashes'
    })
    def all(self, args, file, opts):
        if has_ssdeep:
            fuzzy = self.ssdeep(None, file.sha256_digest)  # pylint: disable=no-value-for-parameter
        else:
            fuzzy = None
        md5_digest = self.md5_digest(None, file.sha256_digest)  # pylint: disable=no-value-for-parameter
        sha1_digest = self.sha1_digest(None, file.sha256_digest)  # pylint: disable=no-value-for-parameter
        sha512_digest = self.sha512_digest(None, file.sha256_digest)  # pylint: disable=no-value-for-parameter

        output = {
            'md5_digest': md5_digest['md5_digest'] if md5_digest is not None else 'n/a',
            'sha1_digest': sha1_digest['sha1_digest'] if sha1_digest is not None else 'n/a',
            'sha256_digest': file.sha256_digest,
            'sha512_digest': sha512_digest['sha512_digest'] if sha512_digest is not None else 'n/a',
            'ssdeep': fuzzy['ssdeep'] if fuzzy is not None else 'n/a'
        }

        return output

    @staticmethod
    def all_markdown(json):
        output = md.table_header(('Hash Type', 'Hash'))
        output += md.table_row(('MD5', json['md5_digest']))
        output += md.table_row(('SHA1', json['sha1_digest']))
        output += md.table_row(('SHA256', json['sha256_digest']))
        output += md.table_row(('SHA512', json['sha512_digest']))
        output += md.table_row(('SSDEEP', json['ssdeep']))
        return output

    @scale.autorun
    @scale.command({
        'info': 'calculates the md5 hash for the file'
    })
    def md5_digest(self, args, file, opts):
        document = db.file_collection.select(file.sha256_digest)
        if 'md5_digest' not in document:
            md5_hash = hashlib.md5()
            with open(file.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            md5_digest = md5_hash.hexdigest()
            data = {'md5_digest': md5_digest}
            if not db.file_collection.update(file.sha256_digest, data):
                raise error.MongoError('error adding md5_digest into file document %s' % file.sha256_digest)
            document = db.file_collection.select(file.sha256_digest)

        return {'md5_digest': document['md5_digest']}

    @staticmethod
    def md5_digest_plaintext(json):
        return json['md5_digest']

    @scale.autorun
    @scale.command({
        'info': 'calculates the sha1 hash for the file'
    })
    def sha1_digest(self, args, file, opts):
        document = db.file_collection.select(file.sha256_digest)
        if 'sha1_digest' not in document:
            sha1_hash = hashlib.sha1()
            with open(file.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha1_hash.update(chunk)
            sha1_digest = sha1_hash.hexdigest()
            data = {'sha1_digest': sha1_digest}
            if not db.file_collection.update(file.sha256_digest, data):
                raise error.MongoError('error adding sha1_digest into file document %s' % file.sha256_digest)
            document = db.file_collection.select(file.sha256_digest)

        return {'sha1_digest': document['sha1_digest']}

    @staticmethod
    def sha1_digest_plaintext(json):
        return json['sha1_digest']

    @scale.autorun
    @scale.command({
        'info': 'calculates the sha512 hash for the file'
    })
    def sha512_digest(self, args, file, opts):
        document = db.file_collection.select(file.sha256_digest)
        if 'sha512_digest' not in document:
            sha512_hash = hashlib.sha512()
            with open(file.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha512_hash.update(chunk)
            sha512_digest = sha512_hash.hexdigest()
            data = {'sha512_digest': sha512_digest}
            if not db.file_collection.update(file.sha256_digest, data):
                raise error.MongoError('error adding sha512_digest into file document %s' % file.sha256_digest)
            document = db.file_collection.select(file.sha256_digest)

        return {'sha512_digest': document['sha512_digest']}

    @staticmethod
    def sha512_digest_plaintext(json):
        return json['sha512_digest']

    if has_ssdeep:  # Optional Dependency
        @scale.autorun
        @scale.command({
            'info': 'calculates the ssdeep hash for the file'
        })
        def ssdeep(self, args, file, opts):
            document = db.file_collection.select(file.sha256_digest)
            if 'ssdeep' not in document:
                fuzzy = str(pydeep.hash_file(file.file_path), encoding="utf-8")
                data = {'ssdeep': fuzzy}
                if not db.file_collection.update(file.sha256_digest, data):
                    raise error.MongoError('error adding ssdeep hash into file document %s' % file.sha256_digest)
                document = db.file_collection.select(file.sha256_digest)
            return {'ssdeep': document['ssdeep']}

        @staticmethod
        def ssdeep_plaintext(json):
            return json['ssdeep']

        @scale.command({
            'info': 'perform fuzzy hash search on the file passed'
        })
        def fuzzy_search(self, args, file, opts):
            results = []

            fuzzy = bytes(self.ssdeep(None, file.sha256_digest)['ssdeep'], 'utf-8')  # pylint: disable=no-value-for-parameter

            documents = db.file_collection.select_all({'file_type': enums.FileType.FILE})  # Only get file type 'file'
            for document in documents:
                if 'ssdeep' not in document:
                    _ssdeep = self.ssdeep(None, document['sha256_digest'])['ssdeep']  # pylint: disable=no-value-for-parameter
                else:
                    _ssdeep = document['ssdeep']
                _ssdeep = bytes(_ssdeep, 'utf-8')
                if _ssdeep == fuzzy:
                    continue
                score = pydeep.compare(fuzzy, _ssdeep)
                if score > 40:
                    results.append((document['name'],
                                    document['sha256_digest'],
                                    document['file_type'],
                                    pydeep.compare(fuzzy, _ssdeep)))

            output = []
            for result in results:
                output += [(str(result[0]), result[1], '/#/' + result[2] + '/' + result[1], str(result[3]))]

            return output

        @staticmethod
        def fuzzy_search_markdown(json):
            output = md.table_header(('File Name', 'SHA256', 'Match (%)'))
            count = 0
            for j in json:
                output += md.table_row((md.url(str(j[0]), j[2]),
                                        str(j[1]),
                                        str(j[3])))
                count += 1
            if count:
                output += md.paragraph(md.bold('Hits:') + str(count))
            else:
                output += md.table_row(('-', '-', '-'))
                output += md.paragraph(md.bold('Hits:') + '0')
            return output
