# py-sonic #
## INSTALL ##

Installation is fairly simple.  Just do the standard install as root:

    tar -xvzf py-sonic-*.tar.gz
    cd py-sonic-*
    python setup.py install

You can also install directly using *pip* or *easy_install*

    pip install py-sonic

## USAGE ##

This library follows the REST API almost exactly (for now).  If you follow the 
documentation on http://www.subsonic.org/pages/api.jsp or you do a:

    pydoc libsonic.connection

I have also added documentation at http://stuffivelearned.org/doku.php?id=programming:python:py-sonic

## BASIC TUTORIAL ##

This is about as basic as it gets.  We are just going to set up the connection
and then get a couple of random songs.

```python
#!/usr/bin/env python

from pprint import pprint
import libsonic

# We pass in the base url, the username, password, and port number
# Be sure to use https:// if this is an ssl connection!
conn = libsonic.Connection('https://music.example.com' , 'myuser' , 
    'secretpass' , port=443)
# Let's get 2 completely random songs
songs = conn.getRandomSongs(size=2)
# We'll just pretty print the results we got to the terminal
pprint(songs)
```

As you can see, it's really pretty simple.  If you use the documentation 
provided in the library:

    pydoc libsonic.connection

or the api docs on subsonic.org (listed above), you should be able to make use
of your server without too much trouble.

Right now, only plain old dictionary structures are returned.  The plan 
for a later release includes the following:

* Proper object representations for Artist, Album, Song, etc.
* Lazy access of members (the song objects aren't created until you want to
  do something with them)
