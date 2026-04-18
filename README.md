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

## A Note About Proxies
I quick note that the library here does **not** assume any particular port
and/or combination with http scheme (e.g., it is not assumed that https ==
port 443).  Given that, the port number is **always** part of the full url.
Why is this important?

The behavior of `urllib` is to use everything up to the 1st "/" as the value
for the `Host` header.  Therefore, if you use port 443 with https, say
through a reverse proxy, the host header will end up being
`Host: <domain/ip>:443`.  It's important to note that this is a
different behavior when compared to something like `curl`, which will
strip the port.

Now, the big issue that can occur is when you have a reverse proxy in front of
your Subsonic service, say for SSL termination.  Some/most proxies will use
whatever is in your `Host` header verbatim, which can break "virtual host"
backend lookups.  Personally, I ran into this with `haproxy`.

On the plus side, there are 2 easy fixes:

1. In your call to `libsonic.connection()`, you can set the `Host` header explicitly by passing in `customHeaders={'Host': 'example.con'}` as an option. Obviously, use your domain name there.
2. Add a virtual host to your proxy config that has `<domain>:port` as a backend alias.  This is the approach I took with `haproxy`, but #1 is also pretty simple.
