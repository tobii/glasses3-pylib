# g3pylib
**This library is still in beta.**

A Python client for Glasses3. It handles all the low level details of communication with the Glasses3 websocket API and exposes a Python API which includes all the endpoints in the websocket API of the Glasses3 as well as some extra convenience methods. It also implements streaming with RTSP and service discovery with Zeroconf.

## Installation
To install this package, clone it and use either

`flit install`

or

`pip install .`

To run examples or tests you need some extra dependencies which are installed by default with the `flit` command. If you are using `pip` the extra dependencies can be installed alongside the library with

`pip install '.[test, examples, example-app]'`

## Environment
The tests and examples load the glasses hostname, which by default is the serial number, from the `.env` file in the project root folder.
See example content below:

```
G3_HOSTNAME=tg03b-080200045321
```

You can also specify this variable directly in your environment.

## Examples
The [example folder](examples) contains a few smaller examples showcasing different use cases of the library as well as a larger controller application with a simple GUI.

## Contributing
More information on how to contribute to this project can be found in [CONTRIBUTING.md](CONTRIBUTING.md).

It contains developer guidelines as well as information on how to run tests and enable logging.
