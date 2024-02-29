# HTML help generator for ESU Command Station (ECoS) network protocol

Simple script to generate HTML documentation of the ECoSNet protocol.
The generator connects to the ECoS, by issuing many `help(...)` commands it
downloads the documentation and creates HTML pages including hyperlinks to
make navigation easy.

## Usage

All you need is Python 3.10 or newer and the IP address of your ECoS.

To generate the documentation run e.g.:
```
python3 ecoshelpgenerator.py 192.168.1.230
```

All documentation will be put in the `output` directory.
