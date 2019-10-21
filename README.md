# Snake

Snake is a malware storage zoo that was built out of the need for a centralised and unified storage solution for malicious samples that could seamlessly integrate into the investigation pipeline.
All Snake interaction is done through its RESTful API that draws its power from scales (modules).

Snake is designed to provide just enough information to allow analysts to quickly and efficiently pivot to the most suitable tools for the task at hand.
That being said there will be times where the information provided by Snake is more than sufficient.
It is a Python based application built on top of Tornado and MongoDB.
Scales provide Snake with a variety of functionality from static analysis through to interaction with external services.

For more information, please see: [Wiki](https://github.com/countercept/snake-core/wiki)

# Dependencies

There are a few dependencies to install Snake.

## Required

- LibYAML
- MongoDB 3.4 or greater
- Python 3.5 or greater
- Redis

## Optional

- libfuzzy & ssdeep

# Install

Snake can be installed as follows:

```bash
pip3 install git+https://github.com/countercept/snake-core
```

or

```bash
pip3 install git+https://github.com/countercept/snake-core[ssdeep]  # for fuzzy search support
```

A default Snake install will make the following assumptions:

- Configuration files are stored in `/etc/snake`
- Cache data is stored in `/var/cache/snake`
- Malware sample files are stored in `/var/db/snake`
- Snake logs are stored in `/var/log/snake`
- Snake Pit logs are stored in `/var/log/snake-pit`

Example configurations can be copied with the following:

```bash
export SNAKE_DIR=`python -c 'import imp; print(imp.find_module("snake")[1])'`
cp -Rfn "${SNAKE_DIR}/data/snake" '/etc/snake'
```

System services can be install with the following:

```bash
# Create the configuration files
if [ ! -f '/etc/snake/systemd/snake.conf' ]; then
  cp '/etc/snake/systemd/snake.conf.example' '/etc/snake/systemd/snake.conf'
fi
if [ ! -f '/etc/snake/systemd/snake-pit.conf' ]; then
  cp '/etc/snake/systemd/snake-pit.conf.example' '/etc/snake/systemd/snake-pit.conf'
fi

# Install the services
cp "$SNAKE_DIR/data/systemd/{snake.service,snake-pit.service}" '/etc/systemd/system'

# Enable the services
sudo systemctl daemon-reload
sudo systemctl enable snake-pit
sudo systemctl enable snake
```

Starting the services is sufficent to execute snake

```bash
systemctl start snake_pit  # Workers used for command execution
systemctl start snake      # Snake
```

# Examples

Snake is a RESTful API so the examples below are not pretty, if that happens to be a requirement take a look at Snake Skin (see [snake-skin](https://github.com/countercept/snake-skin)).
As these examples only scratch the surface, for a complete summary of the API take a look at the API documentation (see [API](https://github.com/countercept/snake-core/wiki/api)).

## Submitting a File

```bash
curl 'http://127.0.0.1:5000/upload/file' \
  -F 'file=@/bin/ls' \
  -F 'name=ls' \
  -F 'description=the ls binary' \
  -XPOST

{
 "data": {
  "file": {
   "description": "the ls binary",
   "file_type": "file",
   "magic": "ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, BuildID[sha1]=d4e02b88e596e4f82c6cc62a5bc4ce5827209a49, stripped",
   "mime": "application/x-sharedlib",
   "name": "ls",
   "sha256_digest": "df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755",
   "size": 133584,
   "timestamp": "2018-03-05T15:38:47.473816"
  }
 },
 "status": "success"
}
```

## Using a Scale

Snake can be queried to present information about all the scales installed.

```bash
curl 'http://127.0.0.1:5000/scales'

{
 "data": {
  "scales": [
   {
    "author": "Countercept",
    "components": [
     "commands"
    ],
    "description": "a module to calculate hashes on files",
    "name": "hashes",
    "supports": [
     "file",
     "memory"
    ],
    "version": "1.0"
   },
   {
    "author": "Countercept",
    "components": [
     "commands"
    ],
    "description": "a module to extract strings from files",
    "name": "strings",
    "supports": [
     "file"
    ],
    "version": "1.0"
   },
   {
    "author": "Countercept",
    "components": [
     "upload"
    ],
    "description": "a module to upload files to Snake from arbitrary URLs",
    "name": "url",
    "supports": [
     "file",
     "memory"
    ],
    "version": "1.0"
   }
  ]
 },
 "status": "success"
}
```

Will a scale in mind (strings), it can be queried in order to find out what commands it supports.

```bash
curl 'http://127.0.0.1:5000/scale/strings/commands'

{
 "data": {
  "commands": [
   {
    "args": null,
    "command": "all_strings",
    "formats": [
     "json",
     "plaintext"
    ],
    "info": "This function will return strings found within the file"
   },
   {
    "args": null,
    "command": "interesting",
    "formats": [
     "json",
     "plaintext"
    ],
    "info": "This function will return interesting strings found within the file"
   }
  ]
 },
 "status": "success"
}
```

A command can then be executed on a sample like so.

```bash
curl 'http://127.0.0.1:5000/command?sha256_digest=df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755&scale=strings&command=all_strings' -XPOST

{
 "data": {
  "command": {
   "args": {},
   "asynchronous": false,
   "command": "all_strings",
   "end_time": "2018-03-05T15:46:04.411522",
   "format": "json",
   "output": {
    "strings": [
     "/lib64/ld-linux-x86-64.so.2",
     "libcap.so.2",
     "_ITM_deregisterTMCloneTable",
     "__gmon_start__",
     "_ITM_registerTMCloneTable",
     "_fini",
     "_init",
     "cap_to_text",
     "cap_free",
     "cap_get_file",
     "libc.so.6",
     "fflush",
     "strcpy",
[snip]
     ".dynamic",
     ".got",
     ".data",
     ".bss",
     ".comment",
     ""
    ]
   },
   "scale": "strings",
   "sha256_digest": "df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755",
   "start_time": "2018-03-05T15:46:04.394986",
   "status": "success",
   "timeout": 600,
   "timestamp": "2018-03-05T15:46:04.385559"
  }
 },
 "status": "success"
}
```

# Being Asynchronous

Commands can also be queued asynchronously, here is a demonstration of such.

```bash
curl 'http://127.0.0.1:5000/command?sha256_digest=df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755&scale=strings&command=all_strings&asynchronous=true' -XPOST

{
 "data": {
  "command": {
   "args": {},
   "asynchronous": true,
   "command": "all_strings",
   "format": "json",
   "output": null,
   "scale": "strings",
   "sha256_digest": "df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755",
   "status": "pending",
   "timeout": 600,
   "timestamp": "2018-03-05T15:48:15.119974"
  }
 },
 "status": "success"
}
```

This command can then be queried and the `status` will eventually update.

```bash
curl 'http://127.0.0.1:5000/command?sha256_digest=df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755&scale=strings&command=all_strings'
{
 "data": {
  "command": {
   "args": {},
   "asynchronous": true,
   "command": "all_strings",
   "end_time": "2018-03-05T15:48:15.154993",
   "format": "json",
   "output": {
    "strings": [
[snip]
    ]
   },
   "scale": "strings",
   "sha256_digest": "df285ab34ad10d8b641e65f39fa11a7d5b44571a37f94314debbfe7233021755",
   "start_time": "2018-03-05T15:48:15.131125",
   "status": "success",
   "timeout": 600,
   "timestamp": "2018-03-05T15:48:15.119974"
  }
 },
 "status": "success"
}
```

# Configuration

This contains a summary of the current configuration variables from Snake that are found in `snake.conf`

## Core Settings

| Variable | Default | Description |
| --- | --- | --- |
| address | 127.0.0.1 | The IP address to server Snake on |
| port | 5000 | The port to serve Snake on |
| cache\_dir | '~/.snake/cache' or '/var/cache/snake' | The default location for Snake to cache to (Quick Install/Traditional) |
| file\_db | '~/.snake/files' or '/var/db/snake' | The default location for Snake to store sample in (Quick Install/Traditional) |
| log\_dir | '~/.snake/log/snake' or '/var/log/snake' | The default location for Snake to log to (Quick Install/Traditional) |
| mongodb | 'mongodb://localhost:27017' | The settings for Mongo so that Snake can connect |

## Behavioural Settings

| Variable | Default | Description |
| --- | --- | --- |
| command\_autoruns | True | Allow Snake to run command autoruns on sample upload |
| strip\_extensions | ['inactive', 'infected', 'safety'] | A list of extensions for Snake to strip from a sample name on upload |
| zip\_passwords | ['inactive', 'infected', 'password'] | A list of passwords to automatically try when unzipping password protected samples on upload |

## Additional Settings

| Variable | Default | Description |
| --- | --- | --- |
| snake\_scale\_dirs | [] | A list of paths to manually installed scales |
| http\_proxy | null | The HTTP proxy for Snake to use |
| https\_proxy | null | The HTTPS proxy for Snake to use |

## Celery Settings

This mirror the setting names that Celery use, i.e. they are passed through to Celery.

| Variable | Default | Description |
| --- | --- | --- |
| backend | 'redis://localhost:6379' | The backend for celery to use |
| broker | 'redis://localhost:6379/0' | The broker for celery to use |
