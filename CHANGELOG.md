##8.1.0

Add API Keys as an option for authentication. Several open subsonic servers have deprecated using
username and password combinations for authentication and want to use API keys instead.

##8.0.1

Add AsyncIO compatible AsyncConnection class for use in async event loops without jumping through
hoops.

##7.0.4

Check for 'playlist' item inside 'playlists' when invoking get_playlists end point. Not all servers
include an empty array and some omit the internal key entirely. Protect against raising a KeyError
by checking for presence.

##7.0.3

Remove insecure flag from Connection object. This was vestigial from the Requests library refactor
and was not used. Remove it to be clear that this is not supported.

##7.0.2

Cleanup strict type checking errors.

##7.0.1

Our PodcastStatus Enum cannot be a data class

##7.0.0

Move to a more pythonic interface. This update drops all camelCasing and moves to more modern python
where we can (f-strings instead of format() etc.). It's another sizeable udpate but should be better
for some value of better.

##6.0.2

Remove @deprecated decorator for now, this makes python 3.13 a requirement and I want to support 3.12

##6.0.1

Remove debug print from getOpenSubsonicExtensions() call

##6.0.0

Major changes. In this update we move to using dataclasses and the mashumaro
serialization mixins to better model the data objects we exchange with the server.
We now have a response type in media.media_types.py for every object that can be
returned according to the open subsonic spec. We also add type information to the
Connection class and its member methods.

This is a breaking change and will require users to update the objects used.

##5.3.1

Silly typo in song.py
Import Connection to make the example script work

##5.3.0

Add transcoding fields to song
Don't throw an exception when the URL does not contain a protocol header


##5.2.1

Add missing comma in song.py because dufus

##5.2.0

Remove warning on missing artist Sort Name field as this field is not required by the
spec. Include disc number in tracks to handle multi-disc albums.

##5.1.1

Relax requirement on responses package.

##5.1.0

Move the starred field up to MediaBase giving all media items the ability to be
starred. It is possible that Podcast Channels cannot be starred in the spec but this
should not cause serious issue.

##5.0.5

Use more sane default values when getting a required key

##5.0.4

Convert getTopSongs, getSimilarSongs[2], and getNewestPodcasts to use media objects
for their return values. Add timeouts to requests.

##5.0.3

More packaging fiddly bits

##5.0.2

Fix ArtistInfo construction, all fields are optional.

##5.0.1

Protect against empty album lists in getAlbumList*

##5.0.0

Fix Album object to align to open subsonic specification, also update Artist object

##4.0.7

Fix path handling for empty and trailing / cases.

##4.0.6

Check the http status code before trying to use the Response object.

##4.0.5

Fiddly bits of packaging...

##4.0.4

Protect against missing headers in response

##4.0.3

More Requests transition bug fixing

##4.0.2

Set the stream parameter when requesting binary data

##4.0.1

Fix search[3|2] output generation

##4.0.0

Switch to the requests library instead of urllib for interaction. Some quality of life improvements on parsing returned objects.

##3.0.7

Objects that contain lists now protect against those lists actually being None in constructors

##3.0.6

Objects missing required fields now report a warning using the warnings module instead of raising a
KeyError.

##3.0.5

Fat fingered a release...

##3.0.3

Give most objects a to_dict() method for easier dumping of values

##3.0.2

Acutally bump _version.py

##3.0.1

Remove accidental print statement in search3 return path, fix song parsing

##3.0.0

Use new media.Playlist object for interacting with playlists. All status only returns now return True on success.

##2.0.1

Fix result parsing in search3, allow for empty artist, album, or song field.

## 2.0.0

Create objects for many of the returns from the api end points and rewored Connection object to use these new classes.

## 1.0.1

Python packaging learning curve. The previous version seems to have built empty
libraries, hopefully this has fixed the problem.

## 1.0.0

Initial release of forked library with Open Subsonic endpoint extensions supported.
