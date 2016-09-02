Zato service deployment scripts
===============================

Script: main.py
Usage: zato-deploy
Configuration: deploy.conf
Purpose: executes all scripts listed below in the given order:

* createsecdefs
* createoutgoings
* storesettings
* uploadmodules
* createchannels

It also reads the file 'extra_paths.txt' (if it exists) and creates symbolic
links for all paths listed therein in the ``zato_extra_paths`` directory. This
step is executed first.


Script: createsecdefs.py
Usage: zato-createsecdefs
Configuration: deploy.conf, secdefs.conf
Purpose: create security definitions in the Zato cluster or updates them (HTTP
Basic Auth only)


Script: createchannels.py
Usage: zato-createchannels
Configuration: deploy.conf, channels.conf
Purpose: creates/updates (incoming) channels (plain HTTP/SOAP) in the Zato
cluster


Script: createoutgoings.py
Usage: zato-createoutgoings
Configuration: deploy.conf, outgoings.conf
Purpose: creates/updates outgoings (plain HTTP/SOAP) in the Zato cluster


Script: deleteservices.py
Usage: zato-deleteservices
Configuration: undeploy.conf
Purpose: deletes services in the Zato cluster (i.e. un-deployment)


Script: uploadmodules.py
Usage: zato-uploadmodules
Configuration: deploy.conf
Purpose: uploads Zato service Python module code files to the Zato cluster
(hot-deployment)


Script: storesettingss.py
Usage: zato-storesettings
Configuration: deploy.conf, settings.conf
Purpose: creates/updates Zato service configuration settings in Redis DB


Published under the MIT license, see LICENSE.txt for details
