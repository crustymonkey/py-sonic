# py-opensonic #

A python library for interacting with an Open Subsonic API implementation.
This started its life as the [py-sonic](https://github.com/crustymonkey/py-sonic) library.
I have tested with Gonic (and continue to do so against each stable docker
release). Please open issues if you discover problems with other implementations.

As of 9.0.0 we use [unasync](https://github.com/python-trio/unasync/) to generate the synchronous
Connection class from the Async one. This will stop us from having to maintain duplicate code in
the two classes. If you submit a PR that changes the Async class, please be sure to run
scripts/gen_sync.py and add the resulting changes to the synchronous class as well.

Any PRs that change the synchronous class by hand or without updating the asynchronous one and/or
the gen_sync.py script will be immediately closed.

As of 8.0.0 this library now offers an AsyncConnection object that uses aiohttp for all
its http requests. It does not create an event loop so is usable inside any application
built on asyncio. The Connection object will continue to use synchronous IO and will
remain for backward compatibility.

## INSTALL ##

Installation is fairly simple.  Just do the standard install as root:

    tar -xvzf py-opensonic-*.tar.gz
    cd py-opensonic-*
    python setup.py install

You can also install directly using *pip* or *easy_install*

    pip install py-opensonic

## USAGE ##

This library follows the REST API almost exactly (for now).  If you follow the 
documentation on https://opensubsonic.netlify.app/docs/ or you do a:

    pydoc libopensonic.connection

The py-sonic original author has added documentation at
http://stuffivelearned.org/doku.php?id=programming:python:py-sonic

## BASIC TUTORIAL ##

This is about as basic as it gets.  We are just going to set up the connection
and then get a couple of random songs.

```python
#!/usr/bin/env python

import libopensonic

# We pass in the base url, the username, password, and port number
# Be sure to use https:// if this is an ssl connection!
conn = libopensonic.Connection('https://music.example.com' , 'myuser' , 
    'secretpass' , port=443)
# Let's get 2 completely random songs
songs = conn.get_random_songs(size=2)
# We'll just pretty print the results we got to the terminal
print(songs[0])
print(songs[1])
```

As you can see, it's really pretty simple.  If you use the documentation 
provided in the library:

    pydoc libopensonic.connection

or the api docs on opensubsonic.netlify.app (listed above), you should be
able to make use of your server without too much trouble.

## Async/Sync Cohabitation ##

As of 9.0.0 we use [unasync](https://github.com/python-trio/unasync/) to generate the synchronous
Connection class from the Async one. This will stop us from having to maintain duplicate code in
the two classes. If you submit a PR that changes the Async class, please be sure to run
scripts/gen_sync.py and add the resulting changes to the synchronous class as well.

Any PRs that change the synchronous class by hand or without updating the asynchronous one and/or
the gen_sync.py script will be immediately closed.
